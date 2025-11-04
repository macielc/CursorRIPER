import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout } from 'antd';
import ptBR from 'antd/locale/pt_BR';

// Pages
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Monitor from './pages/Monitor';
import History from './pages/History';

// Layout components
import Sidebar from './components/Sidebar';
import Header from './components/Header';

const { Content } = Layout;

function App() {
  return (
    <ConfigProvider locale={ptBR}>
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          <Sidebar />
          <Layout>
            <Header />
            <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/strategies" element={<Strategies />} />
                <Route path="/monitor" element={<Monitor />} />
                <Route path="/history" element={<History />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;

