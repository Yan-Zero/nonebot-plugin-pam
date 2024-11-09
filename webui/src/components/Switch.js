import React, { useState } from "react";
import styled from "styled-components";

const SwitchWrapper = styled.div`
  width: 50px;
  height: 28px;
  border-radius: 14px;
  background-color: ${({ is_on }) => (is_on ? "#4cd964" : "#e5e5ea")};
  position: relative;
  transition: background-color 0.3s;
  cursor: pointer;
  display: flex;
  align-items: center;
`;

const SwitchCircle = styled.div`
  width: 24px;
  height: 24px;
  background-color: #ffffff;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: ${({ is_on }) => (is_on ? "24px" : "2px")};
  transition: left 0.3s;
  box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.3);
`;

function Switch({ isOn, onChange }) {
  const [_isOn, setIsOn] = useState(false);

  const toggleSwitch = () => {
    if (onChange) onChange(!(isOn ?? _isOn));
    setIsOn(!(isOn ?? _isOn));
  };

  return (
    <SwitchWrapper is_on={(isOn ?? _isOn) ? 1 : 0} onClick={toggleSwitch}>
      <SwitchCircle is_on={(isOn ?? _isOn) ? 1 : 0} />
    </SwitchWrapper>
  );
}

export default Switch;
