import requests
from bs4 import BeautifulSoup
import re
import time

def fetch_reviews(org_id):
    url = f"https://yandex.ru/maps/org/{org_id}/reviews/"
    headers = {'User-Agent': 'Mozilla/5.0'}  # Чтобы избежать блокировок
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []  # Обработка ошибок
    soup = BeautifulSoup(response.text, 'html.parser')
    reviews = []
    #print(response.text)
    time.sleep(1)
    for review in soup.find_all('div', class_='business-reviews-card-view__review'):
        #print(review)
        text = review.find('span', class_='spoiler-view__text-container').text
        #print(text)
        rating_text = review.find('div', class_='business-rating-badge-view__stars').get('aria-label')  # Парсите рейтинг
        rating_match = re.search(r'\d+', rating_text)
        rating = int(rating_match.group()) if rating_match else 0
        #print(rating)

        #if isinstance(rating, int): print("Переменная x является целым числом")

        date = review.find('span', class_='business-review-view__date').text
        #print(date)
        reviews.append({'text': text, 'rating': rating, 'date': date})
        #print(reviews)
    
    return reviews

#fetch_reviews("1297472925")