import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider, theme } from 'antd';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import DataUpload from './pages/DataUpload';
import SentimentAnalysis from './pages/SentimentAnalysis';
import ChurnPrediction from './pages/ChurnPrediction';
import ExplainableAI from './pages/ExplainableAI';
import RetentionStrategies from './pages/RetentionStrategies';
import './App.css';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
          fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        },
        algorithm: theme.defaultAlgorithm,
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Sidebar />
        <Layout style={{ marginLeft: 250, minHeight: '100vh' }}>
            <Content style={{ 
              margin: '24px 24px 0', 
              overflow: 'initial',
              minHeight: 'calc(100vh - 64px)'
            }}>
              <div className="site-layout-background" style={{ 
                padding: 24, 
                minHeight: '100%',
                borderRadius: 8,
                background: '#fff',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)'
              }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/upload" element={<DataUpload />} />
                  <Route path="/sentiment" element={<SentimentAnalysis />} />
                  <Route path="/churn" element={<ChurnPrediction />} />
                  <Route path="/explainable" element={<ExplainableAI />} />
                  <Route path="/strategies" element={<RetentionStrategies />} />
                </Routes>
              </div>
            </Content>
            <Layout.Footer style={{ textAlign: 'center' }}>
              Retention AI ©{new Date().getFullYear()} - Customer Retention Analytics Platform
            </Layout.Footer>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
};

export default App;
