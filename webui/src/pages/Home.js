import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import styled, { createGlobalStyle } from 'styled-components';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: Arial, sans-serif;
  }

  body {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background-color: #f5f5f5;
  }
`;

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100vh;
`;

function HomePage() {
    return (
        <AppContainer>
            <GlobalStyle />
            <Header />
            {/* <MainContent /> */}
            <Footer />
        </AppContainer>
    );
}

export default HomePage;