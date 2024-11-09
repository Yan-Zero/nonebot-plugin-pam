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
import { produce } from "immer";

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
  const [info, setInfo] = useState(null);

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
    var command = choose?.command;
    if (!command) command = "__all__";

    try {
      if (rules?.[choose.plugin]?.[command]) {
        const rule = rules[choose.plugin][command][0];
        if (rule?.ratelimit === "" && rule?.rule === "True") return false;
      }
    } catch (e) {
      console.log(e);
      setError("未知错误哦。");
    }
    return true;
  }

  function onSwitch(value) {
    if (!choose) {
      setError("请选择一个插件或命令。");
      setTimeout(() => {
        setError(null);
      }, 1500);
      return;
    }
    var command = choose?.command;
    if (!command) command = "__all__";

    if (value) {
      axios
        .post(
          "/pam/api/remove",
          {
            plugin: choose.plugin,
            command: command,
            index: 0,
          },
          {
            headers: {
              Authorization: getAuthToken(),
            },
          }
        )
        .then((response) => {
          if (response.data.success) {
            setRules(
              produce(rules, (draft) => {
                const itemObj = draft?.[choose.plugin]?.[command];
                if (itemObj) {
                  itemObj.shift();
                }
              })
            );
          } else {
            setError(response.data.message);
            setTimeout(() => {
              setError(null);
            }, 1500);
          }
        })
        .catch((error) => {
          console.log(error);
          setError(error.response.data.message);
          setTimeout(() => {
            setError(null);
          }, 1500);
        });
    } else {
      axios
        .post(
          "/pam/api/add",
          {
            plugin: choose.plugin,
            command: command,
            index: 0,
            checker: {
              rule: "True",
              reason:
                command === "__all__"
                  ? `插件${choose?.command ? choose.name : choose.plugin}被关掉了。`
                  : `指令${command}被关掉了。`,
              ratelimit: "",
            },
          },
          {
            headers: {
              Authorization: getAuthToken(),
            },
          }
        )
        .then((response) => {
          if (response.data.success) {
            setRules(
              produce(rules, (draft) => {
                const itemObj = draft?.[choose.plugin]?.[command];
                if (itemObj) {
                  itemObj.unshift({
                    rule: "True",
                    reason:
                      command === "__all__"
                        ? `插件${
                            choose?.command ? choose.name : choose.plugin
                          }被关掉了。`
                        : `指令${command}被关掉了。`,
                    ratelimit: "",
                  });
                } else {
                  draft[choose.plugin][command] = [
                    {
                      rule: "True",
                      reason:
                        command === "__all__"
                          ? `插件${
                              choose?.command ? choose.name : choose.plugin
                            }被关掉了。`
                          : `指令${command}被关掉了。`,
                      ratelimit: "",
                    },
                  ];
                }
              })
            );
          } else {
            setError(response.data.message);
            setTimeout(() => {
              setError(null);
            }, 1500);
          }
        })
        .catch((error) => {
          console.log(error);
          setError(error.response.data.message);
          setTimeout(() => {
            setError(null);
          }, 1500);
        });
    }
  }

  return (
    <AppContainer>
      <GlobalStyle />
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
          {error && (
            <AlertBox
              type="error"
              message={error}
              onClose={() => setError(null)}
            />
          )}
          {info && (
            <AlertBox
              type="info"
              message={info}
              onClose={() => setInfo(null)}
            />
          )}
        </div>
      </div>
      <Footer />
    </AppContainer>
  );
}

export default HomePage;
