import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  ThunderboltOutlined,
  MonitorOutlined,
  HistoryOutlined,
  SettingOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard'
    },
    {
      key: '/strategies',
      icon: <ThunderboltOutlined />,
      label: 'Estrategias'
    },
    {
      key: '/monitor',
      icon: <MonitorOutlined />,
      label: 'Monitor'
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: 'Historico'
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Configuracoes'
    }
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Sider
      width={200}
      style={{
        background: '#001529'
      }}
    >
      <div
        style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: '18px',
          fontWeight: 'bold'
        }}
      >
        MacTester
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        theme="dark"
        style={{ height: '100%', borderRight: 0 }}
      />
    </Sider>
  );
}

export default Sidebar;

