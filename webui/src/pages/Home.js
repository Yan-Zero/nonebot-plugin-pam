import axios from "axios";
import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import MultiLevelList from "../components/ListContainer";
import AlertBox from "../components/AlertBox";
import LoadingPage from "./Loading";
import styled, { createGlobalStyle } from "styled-components";

import checkAuthKey from "../utils";

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
          },
        );
        const plugins = pluginsResponse.data.data;
        const GRules = {};

        await Promise.all(
          Object.keys(plugins).map(async (plugin) => {
            const rulesResponse = await axios.post(
              "/pam/api/fetch",
              { plugin },
              {
                headers: {
                  Authorization: getAuthToken(),
                },
              },
            );
            const rules = rulesResponse.data.data;
            GRules[plugin] = rules;
          }),
        );

        const formattedData = Object.keys(plugins).map((pluginId) => {
          const plugin = plugins[pluginId];
          const children = GRules[pluginId]
            ? Object.keys(GRules[pluginId]).map((command) => ({
                id: `${pluginId}-${command}`,
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

        setData(formattedData);
      } catch (error) {
        console.error("Error fetching plugins or rules:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlugins();
  }, []);

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
            padding: "15px 20px 0 5px",
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
                console.log(choose);
              }}
            />
          )}
        </div>
        <div
          style={{
            padding: "30px",
            flex: "auto",
          }}
        >
          <Header />
        </div>
      </div>
      <Footer />
    </AppContainer>
  );
}

export default HomePage;
