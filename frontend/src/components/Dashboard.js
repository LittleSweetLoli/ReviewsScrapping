import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Dashboard = ({ token, onLogout }) => {
  const [orgId, setOrgId] = useState('');
  const [orgs, setOrgs] = useState([]);  // Список добавленных org_id
  const [selectedReviews, setSelectedReviews] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  
  const [widgetCode, setWidgetCode] = useState('');
  const [showWidgetModal, setShowWidgetModal] = useState(false);

  const generateWidget = (selectedId) => {
    const code = `
<div id="reviews-widget"></div>
<script src="http://localhost:5000/widget.js" 
        data-org-id="${selectedId}" 
        data-limit="5" 
        data-theme="light" 
        data-container="reviews-widget">
</script>
    `.trim();
    setWidgetCode(code);
    setShowWidgetModal(true);
  };


  // Загрузка списка org_id при загрузке дашборда
  useEffect(() => {
    loadOrgs();
  }, []);

  const loadOrgs = async () => {
    try {
      // Здесь можно добавить API-эндпоинт GET /api/orgs для списка, но для MVP симулируем
      // В реальности: axios.get('/api/orgs', { headers: { Authorization: `Bearer ${token}` } })
      setOrgs([{ id: '1297472925', name: 'Test Org \"1297472925\"' }]);  // Заглушка, замените на реальный запрос
    } catch (err) {
      setError('Ошибка загрузки организаций');
    }
  };

  const addOrg = async () => {
    try {
      const res = await axios.post('http://localhost:5000/api/add-org', { org_id: orgId }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrgs([...orgs, { id: orgId, name: `Org ${orgId}` }]);
      setOrgId('');
      alert(`Добавлено: ${res.data.reviews_count} отзывов`);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка добавления');
    }
  };

  const loadReviews = async (selectedId) => {
    try {
      const res = await axios.get(`http://localhost:5000/api/reviews/${selectedId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedReviews(res.data.reviews);
      setSelectedOrgId(selectedId);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка загрузки отзывов');
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Дашборд</h1>
        <button onClick={onLogout} className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
          Выйти
        </button>
      </div>

      {/* Добавление org_id */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Добавить организацию</h2>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="ID организации (например, 1176587986)"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
            className="flex-1 p-3 border rounded-md"
          />
          <button onClick={addOrg} className="bg-blue-500 text-white px-6 py-3 rounded-md hover:bg-blue-600">
            Добавить
          </button>
        </div>
      </div>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      {/* Список org_id */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Ваши организации</h2>
        <ul className="space-y-2">
          {orgs.map((org) => (
            <li key={org.id} className="flex justify-between p-3 bg-gray-50 rounded">
              <span>{org.name || org.id}</span>
              <button
                onClick={() => loadReviews(org.id)}
                className="bg-green-500 text-white px-4 py-1 rounded hover:bg-green-600"
              >
                Загрузить отзывы
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Отзывы */}
      {selectedReviews.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Отзывы для {selectedOrgId}</h2>
          <p className="mb-4">Средний рейтинг: {selectedReviews.reduce((sum, r) => sum + parseFloat(r.rating || 0), 0) / selectedReviews.length}</p>
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto border-collapse">
              <thead>
                <tr className="bg-gray-200">
                  <th className="border p-2">Текст</th>
                  <th className="border p-2">Рейтинг</th>
                  <th className="border p-2">Дата</th>
                </tr>
              </thead>
              <tbody>
                {selectedReviews.map((review, index) => (
                  <tr key={index}>
                    <td className="border p-2">{review.text}</td>
                    <td className="border p-2">{review.rating}</td>
                    <td className="border p-2">{review.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

        {selectedReviews.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h2 className="text-xl font-semibold mb-4">Генератор виджета</h2>
            <button 
                onClick={() => generateWidget(selectedOrgId)}
                className="bg-purple-500 text-white px-6 py-3 rounded-md hover:bg-purple-600"
            >
                Сгенерировать код виджета
            </button>
            </div>
        )}

        {/*Модалка для копирования кода (используйте HeadlessUI или простой div)*/}
        {showWidgetModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg max-w-lg w-full mx-4">
                <h3 className="text-lg font-bold mb-4">Код виджета</h3>
                <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto mb-4 font-mono">{widgetCode}</pre>
                <div className="flex gap-2">
                <button 
                    onClick={() => {
                    navigator.clipboard.writeText(widgetCode);
                    alert('Код скопирован!');
                    }}
                    className="flex-1 bg-green-500 text-white py-2 rounded hover:bg-green-600"
                >
                    Копировать
                </button>
                <button 
                    onClick={() => setShowWidgetModal(false)}
                    className="flex-1 bg-gray-500 text-white py-2 rounded hover:bg-gray-600"
                >
                    Закрыть
                </button>
                </div>
            </div>
            </div>
        )}

    </div>
  );
};

export default Dashboard;