import React from 'react';
import styled from 'styled-components';

const FooterContainer = styled.footer`
  background-color: #333;
  color: #fff;
  text-align: center;
  padding: 10px;
  font-size: 14px;
`;

function Footer() {
    return <FooterContainer>© 2024 Yan-Zero. All rights reserved.</FooterContainer>;
}

export default Footer;
