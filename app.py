from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime, timezone
from config import Config
from scraper import fetch_reviews  # Импорт вашего модуля
from celery import Celery

app = Flask(__name__)
app.config.from_object(Config)

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
db = client['reviews_db']  # Создаст базу автоматически
users = db['users']  # Коллекция для пользователей
orgs = db['orgs']    # Коллекция для организаций и отзывов

# Регистрация пользователя
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')  # В прод: Хешируйте с bcrypt!
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    if users.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 400
    users.insert_one({'email': email, 'password': password})
    return jsonify({'message': 'User registered successfully'}), 201

# Логин и генерация JWT-токена
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = users.find_one({'email': email, 'password': password})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    access_token = create_access_token(identity=email, expires_delta=timedelta(hours=24))
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
        return jsonify({'error': 'Organization not found'}), 404
    return jsonify({
        'reviews': org['reviews'],
        'last_updated': org['last_updated'].isoformat(),
        'average_rating': sum(float(r['rating']) for r in org['reviews']) / len(org['reviews']) if org['reviews'] else 0
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)