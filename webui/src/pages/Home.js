import axios from "axios";
import React, { useState, useEffect } from "react";
import Footer from "../components/Footer";
import MultiLevelList from "../components/ListContainer";
import AlertBox from "../components/AlertBox";
import AppBar from "@mui/material/AppBar";
import LoadingPage from "./Loading";
import styled, { createGlobalStyle } from "styled-components";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import checkAuthKey from "../utils";
import Switch from "../components/Switch";

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
    background-color: #FFF;
  }
`;

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100vh;
`;

function HomePage() {
  const [data, setData] = useState([]);
  const [plugins, setPlugins] = useState({});
  const [rules, setRules] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [choose, setChoose] = useState(null);

  const getAuthToken = () => `Bearer ${checkAuthKey()}`;

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const pluginsResponse = await axios.post(
          "/pam/api/plugins",
          {},
          {
            headers: {
              Authorization: getAuthToken(),
            },
          }
        );
        const _plugins = pluginsResponse.data.data;
        const GRules = {};

        await Promise.all(
          Object.keys(_plugins).map(async (plugin) => {
            const rulesResponse = await axios.post(
              "/pam/api/fetch",
              { plugin },
              {
                headers: {
                  Authorization: getAuthToken(),
                },
              }
            );
            const rules = rulesResponse.data.data;
            GRules[plugin] = rules;
          })
        );

        const formattedData = Object.keys(_plugins).map((pluginId) => {
          const plugin = _plugins[pluginId];
          const children = GRules[pluginId]
            ? Object.keys(GRules[pluginId]).map((command) => ({
                id: `${pluginId}.${command}`,
                name: command,
                plugin: pluginId,
                command,
              }))
            : [];

          return {
            id: pluginId,
            name: plugin.name,
            children,
            plugin: pluginId,
          };
        });
        setPlugins(_plugins);
        setData(formattedData);
        setRules(GRules);
      } catch (error) {
        console.error("Error fetching plugins or rules:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlugins();
  }, []);

  function getEnable() {
    if (!choose) {
      return true;
    }

    if (choose?.command) {
      try {
        if (rules[choose.plugin][choose.command]) {
          const rule = rules[choose.plugin][choose.command][0];
          if (rule?.ratelimit === "" && rule?.rule === "True") return false;
        }
      } catch (e) {
        console.log(e);
        setError("未知错误哦。");
      }
      return true;
    } else {
      try {
        if (rules[choose.plugin]?.__all__) {
          const rule = rules[choose.plugin]?.__all__[0];
          if (rule?.ratelimit === "" && rule?.rule === "True") return false;
        }
      } catch (e) {
        console.log(e);
        setError("未知错误哦。");
      }
      return true;
    }
  }

  function onSwitch(is_on) {
    if (!choose) {
      setError("请选择一个插件或命令。");
      setTimeout(() => {
        setError(null);
      }, 1500);
      return;
    }

    const url = choose.command
      ? `/pam/api/set?plugin=${choose.plugin}&command=${choose.command}`
      : `/pam/api/set?plugin=${choose.plugin}`;

    axios
      .post(
        url,
        {
          rule: is_on ? "False" : "True",
          ratelimit: "",
        },
        {
          headers: {
            Authorization: getAuthToken(),
          },
        }
      )
      .then((response) => {
        if (response.data.status === "success") {
          const updatedRules = { ...rules };
          if (choose.command) {
            updatedRules[choose.plugin][choose.command][0].rule = is_on
              ? "False"
              : "True";
          } else {
            updatedRules[choose.plugin]["__all__"][0].rule = is_on
              ? "False"
              : "True";
          }
          setRules(updatedRules);
        } else {
          setError("更新失败。");
        }
      })
      .catch((error) => {
        console.error("Error updating rule:", error);
        setError("更新时发生错误。");
      });
  }

  return (
    <AppContainer>
      <GlobalStyle />
      {error && (
        <AlertBox type="error" message={error} onClose={() => setError(null)} />
      )}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          height: "100%",
        }}
      >
        <div
          style={{
            width: "25%",
            minWidth: "250px",
            maxWidth: "350px",
            margin: "0",
            padding: "0",
            backgroundColor: "#f5f5f5",
          }}
        >
          {loading ? (
            <LoadingPage /> // 如果 data 为空，渲染 LoadingPage
          ) : (
            <MultiLevelList
              data={data}
              onSelect={(item) => {
                setChoose(item);
              }}
            />
          )}
        </div>
        <div
          style={{
            padding: "15px",
            flex: "auto",
          }}
        >
          <AppBar
            position="static"
            sx={{
              borderRadius: "4px",
            }}
          >
            {" "}
            <Toolbar>
              {/* 标题 */}
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                {choose?.id ? `${choose.name}(${choose.id})` : "PAM"}
              </Typography>
              <Switch isOn={getEnable()} onChange={onSwitch} />
            </Toolbar>
          </AppBar>
          <div
            style={{
              margin: "5px 0 15px 0",
              padding: "10px",
            }}
          ></div>
        </div>
      </div>
      <Footer />
    </AppContainer>
  );
}

export default HomePage;
