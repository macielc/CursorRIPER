import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Typography, Spin, Alert, Button, Space } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { ordersAPI, strategiesAPI } from '../services/api';
import TradingViewChart from '../components/TradingViewChart';
import axios from 'axios';

const { Title } = Typography;

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [todayOrders, setTodayOrders] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [error, setError] = useState(null);
  const [candlesData, setCandlesData] = useState([]);
  const [markers, setMarkers] = useState([]);
  const [chartLoading, setChartLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState(5); // M5 por padrão

  useEffect(() => {
    loadData();
    loadChartData();
    const interval = setInterval(loadData, 10000); // Atualiza a cada 10s
    const chartInterval = setInterval(loadChartData, 10000); // Atualiza grafico a cada 10s
    return () => {
      clearInterval(interval);
      clearInterval(chartInterval);
    };
  }, []);

  // Recarregar gráfico quando timeframe mudar
  useEffect(() => {
    loadChartData();
  }, [selectedTimeframe]);

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

  const loadChartData = async () => {
    try {
      setChartLoading(true);
      
      // Buscar candles e marcadores
      const [candlesRes, markersRes] = await Promise.all([
        axios.get(`http://localhost:8000/api/charts/candles?symbol=WIN$&timeframe=${selectedTimeframe}&bars=500`),
        axios.get('http://localhost:8000/api/charts/markers?limit=100')
      ]);
      
      setCandlesData(candlesRes.data || []);
      setMarkers(markersRes.data || []);
    } catch (err) {
      console.error('Erro ao carregar dados do grafico:', err);
      // Nao mostra erro, grafico simplesmente fica vazio
    } finally {
      setChartLoading(false);
    }
  };

  const handleTimeframeChange = (timeframe) => {
    setSelectedTimeframe(timeframe);
  };

  // Mapa de timeframes disponiveis
  const timeframes = [
    { value: 1, label: 'M1', name: '1 Minuto' },
    { value: 2, label: 'M2', name: '2 Minutos' },
    { value: 5, label: 'M5', name: '5 Minutos' },
    { value: 15, label: 'M15', name: '15 Minutos' },
    { value: 30, label: 'M30', name: '30 Minutos' },
    { value: 60, label: 'H1', name: '1 Hora' },
    { value: 240, label: 'H4', name: '4 Horas' },
    { value: 1440, label: 'D1', name: 'Diário' },
  ];

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

      {/* Grafico de Candles */}
      <Row style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card 
            title={
              <Space>
                <span>WIN$ - {timeframes.find(tf => tf.value === selectedTimeframe)?.label} (500 candles)</span>
              </Space>
            }
            extra={
              <Space>
                <Space.Compact>
                  {timeframes.map((tf) => (
                    <Button
                      key={tf.value}
                      type={selectedTimeframe === tf.value ? 'primary' : 'default'}
                      size="small"
                      onClick={() => handleTimeframeChange(tf.value)}
                      title={tf.name}
                    >
                      {tf.label}
                    </Button>
                  ))}
                </Space.Compact>
                <a onClick={loadChartData}>Atualizar</a>
              </Space>
            }
            loading={chartLoading}
          >
            {candlesData.length > 0 ? (
              <TradingViewChart 
                data={candlesData} 
                markers={markers}
                height={500}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '50px', color: '#888' }}>
                Nenhum dado de grafico disponivel. 
                <br />
                <small>Inicie o backend e certifique-se de que o MT5 esta conectado.</small>
              </div>
            )}
          </Card>
        </Col>
      </Row>
      
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

