import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Очищаем ошибку
    try {
      console.log('Login request:', { email }); // Дебаг: что отправляем
      const res = await axios.post('http://localhost:5000/api/login', 
        { email, password },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      console.log('Login response status:', res.status);  // Должен быть 200
      console.log('Login response data:', res.data);  // Дебаг: что получили

      onLogin(res.data.token);  // Передаём токен в App.js
      navigate('/dashboard');
    } catch (err) {
      console.error('Login error:', err.response?.data || err.message);  // Дебаг: полная ошибка
      setError(err.response?.data?.error || 'Ошибка входа');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Вход</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-3 mb-4 border rounded-md"
          required
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-3 mb-4 border rounded-md"
          required
        />
        <button type="submit" className="w-full bg-green-500 text-white p-3 rounded-md hover:bg-green-600">
          Войти
        </button>
      </form>
      {error && <p className="text-red-500 mt-4 text-center">{error}</p>}
      <p className="mt-4 text-center">
        Нет аккаунта? <a href="/register" className="text-blue-500">Зарегистрироваться</a>
      </p>
    </div>
  );
};

export default Login;