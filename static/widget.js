(function() {
    'use strict';
    
    // Получаем параметры из <script> тега
    const script = document.currentScript;
    const orgId = script ? script.getAttribute('data-org-id') : new URLSearchParams(window.location.search).get('org_id');
    const containerId = script ? script.getAttribute('data-container') || 'reviews-widget' : 'reviews-widget';
    const limit = script ? parseInt(script.getAttribute('data-limit')) || 5 : 5;
    const theme = script ? script.getAttribute('data-theme') || 'light' : 'light';
    
    if (!orgId) {
      console.error('Reviews Widget: org_id required');
      return;
    }
    
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Reviews Widget: Container #${containerId} not found`);
      return;
    }
    
    // Показываем loader
    container.innerHTML = '<div class="reviews-loading">Загрузка отзывов...</div>';
    
    // Fetch данных из API
    fetch(`http://localhost:5000/api/widget/${orgId}?limit=${limit}`)
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return response.json();
      })
      .then(data => {
        if (data.error) throw new Error(data.error);
        
        // Рендерим отзывы
        const reviewsHtml = data.reviews.map((review, index) => `
          <div class="review-card ${theme === 'dark' ? 'bg-gray-800 text-white' : 'bg-white text-black'} p-4 mb-4 border rounded-lg shadow-md">
            <div class="flex items-start mb-2">
              <div class="flex-1">
                <p class="font-semibold mb-1">${review.author || `Отзыв ${index + 1}`}</p>
                <div class="flex items-center mb-2">
                  <span class="text-yellow-500">⭐</span> ${review.rating || 'N/A'}
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 mb-2">${review.date || ''}</p>
            <p class="text-base">${review.text}</p>
          </div>
        `).join('');
        
        // Добавляем заголовок и средний рейтинг
        const headerHtml = `
          <div class="reviews-header mb-4 p-4 bg-blue-100 rounded-lg">
            <h3 class="text-lg font-bold">Отзывы с Яндекс Карт</h3>
            <p class="text-sm text-gray-600">Средний рейтинг: ${data.average_rating.toFixed(1)} / 5</p>
            <p class="text-xs text-gray-500">Обновлено: ${new Date(data.last_updated).toLocaleDateString()}</p>
          </div>
        `;
        
        container.innerHTML = headerHtml + reviewsHtml;
        
        // Если отзывов нет
        if (data.reviews.length === 0) {
          container.innerHTML += '<p class="text-gray-500 italic">Отзывы не найдены.</p>';
        }
      })
      .catch(error => {
        console.error('Reviews Widget Error:', error);
        container.innerHTML = `<div class="text-red-500 p-4">Ошибка загрузки отзывов: ${error.message}</div>`;
      });
  })();