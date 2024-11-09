import React, { useState } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";

// 样式定义
const ListContainer = styled.div`
  font-family: Arial, sans-serif;
`;

const ListItem = styled.li`
  padding: 8px 12px;
  margin: 4px 0;
  background-color: ${(props) => (props.selected ? "#f0f8ff" : "#fff")};
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #f1f1f1;
  }
`;

const SubList = styled.ul`
  margin-top: 8px;
  list-style-type: none;
  padding-left: 20px;
  display: ${(props) => (props.$is_visible ? "block" : "none")};
`;

const ToggleButton = styled.button`
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 14px;
  color: #007bff;
  margin-left: 8px;

  &:focus {
    outline: none;
  }

  &:hover {
    color: #0056b3;
  }
`;

// 组件逻辑
const MultiLevelList = ({ data, onSelect }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [openItems, setOpenItems] = useState({});

  const handleItemClick = (item) => {
    setSelectedItem(item.id);
    if (onSelect) onSelect(item);
  };

  const toggleSubList = (itemId) => {
    setOpenItems((prevState) => ({
      ...prevState,
      [itemId]: !prevState[itemId],
    }));
  };

  const renderListItems = (items) => {
    return items.map((item) => (
      <div key={item.id}>
        <ListItem
          selected={item.id === selectedItem}
          onClick={() => handleItemClick(item)}
        >
          {item.name}
          {item.children && item.children.length > 0 && (
            <ToggleButton onClick={() => toggleSubList(item.id)}>
              {openItems[item.id] ? "[-]" : "[+]"}
            </ToggleButton>
          )}
        </ListItem>
        {item.children && item.children.length > 0 && (
          <SubList $is_visible={openItems[item.id] ? 1 : 0}>
            {renderListItems(item.children)}
          </SubList>
        )}
      </div>
    ));
  };

  return <ListContainer>{renderListItems(data)}</ListContainer>;
};

MultiLevelList.propTypes = {
  data: PropTypes.array,
  onSelect: PropTypes.func,
};

export default MultiLevelList;
