import requests
from bs4 import BeautifulSoup
import re

# def fetch_reviews(org_id):
#     url = f"https://yandex.ru/maps/org/{org_id}/reviews/"
#     headers = {'User-Agent': 'Mozilla/5.0'}  # Чтобы избежать блокировок
#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         return []  # Обработка ошибок
#     soup = BeautifulSoup(response.text, 'html.parser')
#     reviews = []
#     for review in soup.find_all('div', class_='business-reviews-card-view__review'):
#         text = review.find('span', class_='spoiler-view__text-container').text
#         rating = review.find('div', class_='business-rating-badge-view__stars').get('aria-label')  # Парсите рейтинг
#         date = review.find('span', class_='business-review-view__date').text
#         reviews.append({'text': text, 'rating': rating, 'date': date})
#         print(reviews)
#     return reviews

def fetch_reviews(org_id):
    url = f"https://yandex.ru/maps/org/{org_id}/reviews/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    reviews = []
    for review in soup.find_all('div', class_='business-review-view__body'):
        text = review.find('span', class_='business-review-view__body-text').text.strip()
        rating_elem = review.find('div', class_='business-rating-badge-view__stars')
        rating_text = rating_elem['aria-label'] if rating_elem and 'aria-label' in rating_elem.attrs else '0'
        # Извлекаем число из строки вида "Оценка 5 Из 5"
        rating_match = re.search(r'\d+', rating_text)
        rating = float(rating_match.group()) if rating_match else 0.0
        date = review.find('span', class_='business-review-view__date').text.strip()
        reviews.append({'text': text, 'rating': rating, 'date': date})
    return reviews