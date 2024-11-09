// LoadingPage.js
import React from "react";
import styled, { keyframes } from "styled-components";

const rotate = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f4f8;
  font-family: "Arial", sans-serif;
`;

const Loader = styled.div`
  border: 8px solid #f3f3f3;
  border-top: 8px solid #3498db;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: ${rotate} 2s linear infinite;
`;

const LoadingText = styled.p`
  font-size: 1.5rem;
  transform: translateX(0.5rem);
  color: #333;
  margin-top: 20px;
  text-align: center;
`;

const LoadingPage = () => {
  return (
    <LoadingContainer>
      <div
        style={{
          alignItems: "center",
        }}
      >
        <Loader />
        <LoadingText>正在加载...</LoadingText>
      </div>
    </LoadingContainer>
  );
};

export default LoadingPage;
