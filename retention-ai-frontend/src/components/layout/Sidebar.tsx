import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  UploadOutlined,
  BarChartOutlined,
  TeamOutlined,
  BulbOutlined,
  LineChartOutlined,
} from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const location = useLocation();

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: 'Dashboard', path: '/' },
    { key: 'upload', icon: <UploadOutlined />, label: 'Data Upload', path: '/upload' },
    { key: 'sentiment', icon: <BarChartOutlined />, label: 'Sentiment Analysis', path: '/sentiment' },
    { key: 'churn', icon: <TeamOutlined />, label: 'Churn Prediction', path: '/churn' },
    { key: 'explainable', icon: <BulbOutlined />, label: 'Explainable AI', path: '/explainable' },
    { key: 'strategies', icon: <LineChartOutlined />, label: 'Retention Strategies', path: '/strategies' },
  ];

  return (
    <Sider 
      width={250} 
      style={{
        background: '#1a1f2e',
        boxShadow: '2px 0 8px 0 rgba(29, 35, 41, 0.1)',
        position: 'fixed',
        height: '100vh',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 10,
      }}
    >
      <div 
        className="logo" 
        style={{ 
          padding: '20px 16px', 
          color: 'white', 
          textAlign: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <h2 style={{ color: '#fff', margin: 0, fontSize: '20px' }}>Retention AI</h2>
      </div>
      <Menu
        theme="dark"
        mode="inline"
        style={{
          background: 'transparent',
          borderRight: 'none',
          padding: '16px 8px',
        }}
        selectedKeys={[menuItems.find(item => location.pathname === item.path)?.key || 'dashboard']}
      >
        {menuItems.map(item => (
          <Menu.Item key={item.key} icon={item.icon}>
            <Link to={item.path}>{item.label}</Link>
          </Menu.Item>
        ))}
      </Menu>
    </Sider>
  );
};

export default Sidebar;
