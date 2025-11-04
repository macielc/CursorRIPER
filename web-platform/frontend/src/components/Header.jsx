import React, { useState, useEffect } from 'react';
import { Layout, Badge, Space, Typography } from 'antd';
import { ApiOutlined } from '@ant-design/icons';
import { healthCheck } from '../services/api';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

function Header() {
  const [backendStatus, setBackendStatus] = useState('loading');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthCheck();
        setBackendStatus('online');
      } catch (error) {
        setBackendStatus('offline');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check a cada 30s

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (backendStatus) {
      case 'online':
        return 'green';
      case 'offline':
        return 'red';
      default:
        return 'default';
    }
  };

  return (
    <AntHeader
      style={{
        padding: '0 24px',
        background: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 1px 4px rgba(0,21,41,0.08)'
      }}
    >
      <Typography.Title level={4} style={{ margin: 0 }}>
        MacTester Web Platform
      </Typography.Title>

      <Space>
        <Badge status={getStatusColor()} />
        <ApiOutlined />
        <Text type="secondary">
          Backend: {backendStatus === 'online' ? 'Online' : backendStatus === 'offline' ? 'Offline' : 'Checking...'}
        </Text>
      </Space>
    </AntHeader>
  );
}

export default Header;

