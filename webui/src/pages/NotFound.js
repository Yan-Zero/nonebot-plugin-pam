// NotFound.js
import React from "react";
import styled from "styled-components";

// 背景渐变样式
const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #6e7e85, #38464d);
  font-family: "Arial", sans-serif;
  color: white;
  text-align: center;
  animation: fadeIn 1s ease-in-out;
`;

// 标题样式
const Title = styled.h1`
  font-size: 5rem;
  font-weight: bold;
  margin-bottom: 20px;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  animation: fadeIn 1.5s ease-in-out;
`;

// 描述文本样式
const Message = styled.p`
  font-size: 1.5rem;
  margin-bottom: 40px;
  animation: fadeIn 2s ease-in-out;
  opacity: 0.8;
`;

// 按钮样式
const Button = styled.button`
  padding: 15px 30px;
  font-size: 1.2rem;
  background-color: #ff6f61;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition:
    transform 0.3s ease,
    background-color 0.3s ease;

  &:hover {
    transform: scale(1.1);
    background-color: #e45a4b;
  }

  &:active {
    transform: scale(1);
  }
`;

// 动画效果
const fadeIn = `
  @keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
  }
`;

const NotFound = () => {
  return (
    <Container>
      <style>{fadeIn}</style> {/* 动画关键帧 */}
      <div
        style={{
          alignItems: "center",
        }}
      >
        <Title>404</Title>
        <Message>页面未找到</Message>
        <Button onClick={() => (window.location.href = "/pam")}>
          返回首页
        </Button>
      </div>
    </Container>
  );
};

export default NotFound;
