import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Typography, Spin, Alert } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { ordersAPI, strategiesAPI } from '../services/api';

const { Title } = Typography;

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [todayOrders, setTodayOrders] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      const [statsRes, todayRes, strategiesRes] = await Promise.all([
        ordersAPI.stats().catch(() => ({ data: null })),
        ordersAPI.todaySummary().catch(() => ({ data: { orders: [] } })),
        strategiesAPI.list().catch(() => ({ data: [] }))
      ]);
      
      setStats(statsRes.data);
      setTodayOrders(todayRes.data.orders || []);
      setStrategies(strategiesRes.data || []);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
      setError('Erro ao conectar com o backend');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Horario',
      dataIndex: 'created_at',
      key: 'time',
      render: (text) => new Date(text).toLocaleTimeString('pt-BR')
    },
    {
      title: 'Estrategia',
      dataIndex: 'strategy_name',
      key: 'strategy'
    },
    {
      title: 'Simbolo',
      dataIndex: 'symbol',
      key: 'symbol'
    },
    {
      title: 'Tipo',
      dataIndex: 'action',
      key: 'action',
      render: (text) => (
        <span style={{ color: text === 'buy' ? '#3f8600' : '#cf1322' }}>
          {text === 'buy' ? 'COMPRA' : 'VENDA'}
        </span>
      )
    },
    {
      title: 'Preco',
      dataIndex: 'entry_price',
      key: 'price',
      render: (value) => value?.toFixed(2)
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (text) => {
        const statusMap = {
          'pending': 'Pendente',
          'filled': 'Preenchida',
          'tp_hit': 'TP Atingido',
          'sl_hit': 'SL Atingido',
          'closed': 'Fechada'
        };
        return statusMap[text] || text;
      }
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Carregando..." />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>Dashboard</Title>

      {error && (
        <Alert
          message="Erro de Conexao"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Trades Hoje"
              value={todayOrders.length}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="Win Rate"
              value={stats?.win_rate || 0}
              precision={1}
              suffix="%"
              valueStyle={{ color: (stats?.win_rate || 0) >= 50 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="PnL Pontos"
              value={stats?.total_pnl_points || 0}
              precision={2}
              valueStyle={{ color: (stats?.total_pnl_points || 0) > 0 ? '#3f8600' : '#cf1322' }}
              prefix={(stats?.total_pnl_points || 0) > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="Estrategias Ativas"
              value={strategies.filter(s => s.is_active).length}
              suffix={`/ ${strategies.length}`}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Card title="Ordens Hoje" extra={<a onClick={loadData}>Atualizar</a>}>
            <Table
              dataSource={todayOrders}
              columns={columns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: 'Nenhuma ordem hoje' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;

