import React, { useState } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Collapse from "@mui/material/Collapse";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";

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
function MultiLevelList({ data, onSelect }) {
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

  const renderListItems = (items, pl = 2) => {
    return items.map((item) => (
      <div key={item.id}>
        <ListItemButton
          selected={item.id === selectedItem}
          onClick={() => handleItemClick(item)}
          sx={{ pl: pl }}
        >
          <ListItemText primary={item.name} />
          {item.children && item.children.length > 0 && (
            <ToggleButton onClick={() => toggleSubList(item.id)}>
              {openItems[item.id] ? <ExpandLess /> : <ExpandMore />}
            </ToggleButton>
          )}
        </ListItemButton>
        {item.children && item.children.length > 0 && (
          <Collapse in={openItems[item.id]} timeout="auto" unmountOnExit>
            {renderListItems(item.children, pl + 2)}
          </Collapse>
        )}
      </div>
    ));
  };

  return (
    <List
      sx={{
        width: "100%",
        maxWidth: 360,
        bgcolor: "background.paper",
      }}
      component="nav"
      aria-labelledby="nested-list-subheader"
    >
      {renderListItems(data)}
    </List>
  );
}

MultiLevelList.propTypes = {
  data: PropTypes.array,
  onSelect: PropTypes.func,
};

export default MultiLevelList;
