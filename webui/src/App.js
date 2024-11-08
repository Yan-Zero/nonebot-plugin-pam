// App.js
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Cookies from 'js-cookie';

import HomePage from './pages/Home';
import NotFound from './pages/NotFound';
import LoginPage from './pages/Login';
import LoadingPage from './pages/Loading';

import AlertBox from './components/AlertBox';

function App() {
  const [error, setError] = useState(null);
  const [authValidating, setAuthValidating] = useState(true); // 用于指示是否正在验证 auth_key

  // 检查是否存在有效的 auth_key
  const checkAuthKey = () => {
    const authKey = Cookies.get('auth_key');
    return authKey;
  };

  const validateAuthKey = async () => {
    const authKey = checkAuthKey();
    if (authKey) {
      try {
        const response = await fetch('/api/auth', {
          headers: {
            Authorization: `Bearer ${authKey}`
          },
        });
        if (!response.ok) {
          throw new Error('Invalid auth_key');
        }
      } catch (err) {
        setError('似乎登录已经过期。');
        setTimeout(() => {
          window.location.href = '/login';
        }, 3000);
      } finally {
        setAuthValidating(false);
      }
    } else {
      setAuthValidating(false);
      setError('尚未登录。Redirecting to login...');
      setTimeout(() => {
        window.location.href = '/login';
      }, 3000);
    }
  };

  useEffect(() => {
    validateAuthKey();
  }, []);

  return (
    <Router>
      <div>
        {error && <AlertBox type="error" message={error} onClose={() => setError(null)} />}
        <Routes>
          <Route path="/" exact element={authValidating ? <LoadingPage /> : checkAuthKey() ? <HomePage /> : <Navigate to="/login" />}>

          </Route>
          <Route path="/login" element={<LoginPage />} />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
