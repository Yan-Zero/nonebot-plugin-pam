import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';

const slideIn = keyframes`
  0% {
    opacity: 0.5;
    transform: translateY(-100%) translateX(-50%);
  }
  100% {
    transform: translateY(0) translateX(-50%);
    opacity: 1;
  }
`;


const AlertBoxWrapper = styled.div`
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 500px;
  width: 100%;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 16px;

  background-color: ${(props) => props.bgColor || '#2196F3'}; // 默认蓝色
  color: white;

  &.slide-in {
    animation: ${slideIn} 0.5s ease-out;
  }
`;

const CloseButton = styled.button`
  background: transparent;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  margin-left: 15px;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.7;
  }
`;

const AlertBox = ({ message, type, onClose }) => {
  const [isClosed, setIsClosed] = useState(false);

  const getBackgroundColor = () => {
    switch (type) {
      case 'success':
        return '#4CAF50';
      case 'error':
        return '#F44336';
      case 'warning':
        return '#FF9800';
      case 'info':
        return '#2196F3';
      default:
        return '#2196F3';
    }
  };

  const handleClose = () => {
    setIsClosed(true);
    setTimeout(() => {
      if (onClose) onClose();
    }, 500);
  };

  return !isClosed ? (
    <AlertBoxWrapper
      bgColor={getBackgroundColor()}
      className={isClosed ? 'fade-out' : 'slide-in'}
    >
      <span>{message}</span>
      <CloseButton onClick={handleClose}>×</CloseButton>
    </AlertBoxWrapper>
  ) : null;
};

export default AlertBox;
