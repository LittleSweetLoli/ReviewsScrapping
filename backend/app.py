from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime, timezone
from config import Config
from scraper import fetch_reviews  # Импорт вашего модуля
from celery import Celery
from flask_cors import CORS
from flask import send_from_directory

app = Flask(__name__)
app.config.from_object(Config)
# Полная CORS: Разрешаем POST с localhost:3000, JSON headers
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"]
    },
    r"/api/widget/?": {
        "origins": "*",  # Любые домены (в проде: ["https://*.example.com"] для whitelist)
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Type"]
    },
    r"/widget\.js": {
        "origins": "*",
        "methods": ["GET"],
        "allow_headers": []
    }
})

# Инициализация Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)
jwt = JWTManager(app)

client = MongoClient(app.config['MONGODB_URI'])
# try:
#     client = MongoClient(app.config['MONGODB_URI'])
#     client.admin.command('ismaster')  # Тест подключения
#     print("MongoDB connected successfully!")  # Дебаг в логах Flask
# except Exception as e:
#     print(f"MongoDB connection error: {e}")  # Покажет в терминале
#     client = None

db = client['reviews_db']  # Создаст базу автоматически
users = db['users']  # Коллекция для пользователей
orgs = db['orgs']    # Коллекция для организаций и отзывов
# if client:
#     db = client['reviews_db']
#     users = db['users']
#     orgs = db['orgs']
# else:
#     # Fallback: В продакшене — ошибка 500
#     @app.errorhandler(500)
#     def internal_error(error):
#         return jsonify({'error': 'Database unavailable'}), 500

# Регистрация пользователя
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')  # В прод: Хешируйте с bcrypt!
    print(f"Register attempt: {email}")  # Дебаг
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    if users.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 400
    users.insert_one({'email': email, 'password': password})
    print(f"User registered: {email}")  # Дебаг
    return jsonify({'message': 'User registered successfully'}), 201

# Логин и генерация JWT-токена
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(f"Login attempt: {email}")  # Дебаг
    user = users.find_one({'email': email, 'password': password})
    if not user:
        print(f"User not found or wrong password for {email}")  # Дебаг
        return jsonify({'error': 'Invalid credentials'}), 401
    access_token = create_access_token(identity=email, expires_delta=timedelta(hours=24))
    print(f"Token generated for {email}")  # Дебаг
    return jsonify({'token': access_token}), 200

# Добавление организации (с скрапингом)
@app.route('/api/add-org', methods=['POST'])
@jwt_required()
def add_org():
    current_user_email = get_jwt_identity()
    user = users.find_one({'email': current_user_email})
    data = request.get_json()
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id is required'}), 400
    # Проверяем дубликат
    if orgs.find_one({'user_id': user['_id'], 'org_id': org_id}):
        #return jupytext({'error': 'Organization already added'}), 400
        return jsonify({'error': 'Organization already added'}), 400
    try:
        reviews = fetch_reviews(org_id)  # Вызов вашего скрапера
        if not reviews:
            return jsonify({'error': 'No reviews found or scraping failed'}), 404
        orgs.insert_one({
            'user_id': user['_id'],
            'org_id': org_id,
            'reviews': reviews,
            'last_updated': datetime.now(timezone.utc) #datetime.utcnow()
        })
        return jsonify({'message': 'Organization added', 'reviews_count': len(reviews)}), 201
    except Exception as e:
        return jsonify({'error': f'Scraping error: {str(e)}'}), 500

# Получение отзывов по org_id
@app.route('/api/reviews/<org_id>', methods=['GET'])
@jwt_required()
def get_reviews(org_id):
    current_user_email = get_jwt_identity()
    user = users.find_one({'email': current_user_email})
    org = orgs.find_one({'user_id': user['_id'], 'org_id': org_id})
    if not org:
        return jsonify({'error': 'Organization not found', 'message': 'Organization not found'}), 404
    return jsonify({
        'reviews': org['reviews'],
        'last_updated': org['last_updated'].isoformat(),
        'average_rating': sum(float(r['rating']) for r in org['reviews']) / len(org['reviews']) if org['reviews'] else 0
    }), 200

@app.route('/api/widget/<org_id>', methods=['GET'])
def get_widget_data(org_id):
    """Публичный endpoint для виджета — возвращает отзывы без auth."""
    try:
        org = orgs.find_one({'org_id': org_id})
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Опционально: Параметры (лимит, сортировка)
        limit = request.args.get('limit', 5, type=int)
        reviews = org['reviews'][:limit]  # Первые N отзывов
        
        return jsonify({
            'reviews': reviews,
            'org_id': org_id,
            'last_updated': org['last_updated'].isoformat(),
            'average_rating': sum(float(r.get('rating', 0)) for r in reviews) / len(reviews) if reviews else 0
        }), 200
    except Exception as e:
        return jsonify({'error': f'Widget error: {str(e)}'}), 500
    
@app.route('/widget.js')
def serve_widget():
    try:
        return send_from_directory('static', 'widget.js')
    except Exception as e:
        return jsonify({'error': f'Widget error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)