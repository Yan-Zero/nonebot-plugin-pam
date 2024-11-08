import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'; // 导入 useNavigate
import Cookies from 'js-cookie';
import styled from 'styled-components';
import AlertBox from '../components/AlertBox';

// Styled-components
const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(to right, #6a11cb, #2575fc);
`;

const LoginBox = styled.div`
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
  align-items: center;
`;

const Title = styled.h2`
  margin-bottom: 20px;
  font-family: 'Arial', sans-serif;
  font-size: 28px;
  color: #333;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px 15px;
  margin: 7px 0;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
  outline: none;
  position: relative;
  right: 15px;
  &:focus {
    border-color: #2575fc;
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 12px;
  background-color: #2575fc;
  border: none;
  border-radius: 10px;
  margin: 10px 0;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #6a11cb;
  }
`;

// 注册链接
const Footer = styled.p`
  margin-top: 20px;
  font-size: 14px;
  color: #666;
  a {
    color: #2575fc;
    text-decoration: none;
    &:hover {
      text-decoration: underline;
    }
  }
`;

const LoginPage = () => {
    const [username, setName] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const navigate = useNavigate();
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const response = await fetch('/api/auth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (response.ok) {
                Cookies.set('auth_key', data.auth_key, { expires: 7, secure: true });
                setSuccess('登录成功，正在跳转到首页...');
                navigate('/'); // 跳转到首页
            } else {
                if (response.status === 401) {
                    setError('账号或密码错误');
                } else {
                    setError(data.message || '未知错误');
                }
            }
        } catch (error) {
            setError('登录时发生错误');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container>
            <LoginBox>
                <Title>PAM</Title>

                <form onSubmit={handleSubmit}>
                    <Input
                        type="text"
                        placeholder="User Name"
                        value={username}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                    <Input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                    {error && <AlertBox type="error" message={error} onClose={() => setError(null)} />}
                    {success && <AlertBox type="success" message={success} onClose={() => setSuccess(null)} />}
                    <Button type="submit" disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                    </Button>
                </form>
                <Footer>
                    © 2024 Yan-Zero. All rights reserved.
                </Footer>
            </LoginBox>
        </Container>
    );
};

export default LoginPage;
