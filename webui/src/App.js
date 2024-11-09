// App.js
import React, { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
  useLocation,
} from "react-router-dom";

import HomePage from "./pages/Home";
import NotFound from "./pages/NotFound";
import LoginPage from "./pages/Login";
import LoadingPage from "./pages/Loading";

import AlertBox from "./components/AlertBox";

import checkAuthKey from "./utils";

function AppContent() {
  const [error, setError] = useState(null);
  const [authValidating, setAuthValidating] = useState(true);
  const location = useLocation(); // 确保在 Router 内部使用 useLocation

  const validateAuthKey = async () => {
    const authKey = checkAuthKey();
    if (authKey) {
      try {
        const response = await fetch("/pam/api/auth", {
          headers: {
            Authorization: `Bearer ${authKey}`,
          },
        });
        if (!response.ok) {
          throw new Error("Invalid auth_key");
        }
      } catch (_) {
        console.log(_);
        setError("似乎登录已经过期。");
        setTimeout(() => {
          window.location.href = "/pam/login";
        }, 3000);
      } finally {
        setAuthValidating(false);
      }
    } else {
      setAuthValidating(false);
      setError("尚未登录。Redirecting to login...");
      setTimeout(() => {
        window.location.href = "/pam/login";
      }, 3000);
    }
  };

  useEffect(() => {
    // 当路径不是 /pam/login 时才执行验证
    if (location.pathname !== "/pam/login") {
      validateAuthKey();
    } else {
      setAuthValidating(false); // 避免在 login 页加载时显示加载状态
    }
  }, [location.pathname]);

  return (
    <div>
      {error && (
        <AlertBox type="error" message={error} onClose={() => setError(null)} />
      )}
      <Routes>
        <Route
          path="/pam"
          exact
          element={
            authValidating ? (
              <LoadingPage />
            ) : checkAuthKey() ? (
              <HomePage />
            ) : (
              <Navigate to="/pam/login" />
            )
          }
        ></Route>
        <Route path="/pam/login" element={<LoginPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
