import React from "react";
import styled from "styled-components";

const HeaderContainer = styled.header`
  background-color: #333;
  color: #fff;
  text-align: center;
  padding: 20px;
  font-size: 24px;
`;

function Header() {
  return <HeaderContainer>Policy and Access Manager</HeaderContainer>;
}

export default Header;
