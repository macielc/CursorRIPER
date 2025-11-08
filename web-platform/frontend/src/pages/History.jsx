import React, { useState, useEffect } from 'react';
import { Card, Table, DatePicker, Select, Space, Typography, Button, Tag, Row, Col } from 'antd';
import { ReloadOutlined, DownloadOutlined, SearchOutlined, ClearOutlined } from '@ant-design/icons';
import { ordersAPI, strategiesAPI } from '../services/api';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

function History() {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [filters, setFilters] = useState(() => {
    // Carregar filtros salvos do localStorage
    const savedFilters = localStorage.getItem('history_filters');
    if (savedFilters) {
      const parsed = JSON.parse(savedFilters);
      // Converter strings de data de volta para dayjs
      if (parsed.dateRange) {
        parsed.dateRange = [dayjs(parsed.dateRange[0]), dayjs(parsed.dateRange[1])];
      }
      return parsed;
    }
    return {
      dateRange: null,
      symbol: null,
      strategy: null,
      status: null
    };
  });

  useEffect(() => {
    loadStrategies();
    loadOrders();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await strategiesAPI.list();
      setStrategies(response.data || []);
    } catch (error) {
      console.error('Erro ao carregar estrategias:', error);
    }
  };

  const loadOrders = async () => {
    try {
      setLoading(true);
      
      // Preparar parametros para a API (nomes devem coincidir com backend)
      const params = {};
      
      if (filters.dateRange && filters.dateRange[0] && filters.dateRange[1]) {
        params.date_from = filters.dateRange[0].format('YYYY-MM-DD');
        params.date_to = filters.dateRange[1].format('YYYY-MM-DD');
      }
      
      if (filters.symbol) params.symbol = filters.symbol;
      if (filters.strategy) params.strategy_name = filters.strategy;
      if (filters.status) params.status = filters.status;
      
      const response = await ordersAPI.list(params);
      setOrders(response.data || []);
    } catch (error) {
      console.error('Erro ao carregar historico:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    // Salvar filtros no localStorage
    const filtersToSave = { ...filters };
    if (filtersToSave.dateRange) {
      filtersToSave.dateRange = [
        filtersToSave.dateRange[0].format('YYYY-MM-DD'),
        filtersToSave.dateRange[1].format('YYYY-MM-DD')
      ];
    }
    localStorage.setItem('history_filters', JSON.stringify(filtersToSave));
    
    // Buscar ordens
    loadOrders();
  };

  const handleClearFilters = () => {
    const emptyFilters = {
      dateRange: null,
      symbol: null,
      strategy: null,
      status: null
    };
    setFilters(emptyFilters);
    localStorage.removeItem('history_filters');
    
    // Recarregar sem filtros
    setTimeout(() => loadOrders(), 100);
  };

  const columns = [
    {
      title: 'Data/Hora',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString('pt-BR')
    },
    {
      title: 'Estrategia',
      dataIndex: 'strategy_name',
      key: 'strategy_name'
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
        <Tag color={text === 'buy' ? 'green' : 'red'}>
          {text === 'buy' ? 'COMPRA' : 'VENDA'}
        </Tag>
      )
    },
    {
      title: 'Entrada',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (value) => value?.toFixed(2)
    },
    {
      title: 'Saida',
      dataIndex: 'exit_price',
      key: 'exit_price',
      render: (value) => value ? value.toFixed(2) : '-'
    },
    {
      title: 'Resultado',
      dataIndex: 'pnl_points',
      key: 'resultado',
      align: 'center',
      render: (value) => {
        if (value === null || value === undefined) return '-';
        const isGain = value > 0;
        const color = isGain ? '#52c41a' : '#ff4d4f'; // Verde: #52c41a, Vermelho: #ff4d4f
        const text = isGain ? 'GAIN' : 'LOSS';
        return (
          <span style={{ 
            color: color, 
            fontWeight: 600,
            fontSize: '13px'
          }}>
            {text}
          </span>
        );
      }
    },
    {
      title: 'Pts',
      dataIndex: 'pnl_points',
      key: 'pnl_points',
      align: 'right',
      render: (value) => {
        if (value === null || value === undefined) return '-';
        const color = value > 0 ? '#52c41a' : value < 0 ? '#ff4d4f' : 'default';
        const sign = value > 0 ? '+' : '';
        return <span style={{ color, fontWeight: 500 }}>{sign}{value.toFixed(2)}</span>;
      }
    },
    {
      title: 'PnL (R$)',
      dataIndex: 'pnl_currency',
      key: 'pnl_currency',
      align: 'right',
      render: (value) => {
        if (value === null || value === undefined) return '-';
        const color = value > 0 ? '#52c41a' : value < 0 ? '#ff4d4f' : 'default';
        return (
          <span style={{ color, fontWeight: 600 }}>
            {value.toLocaleString('pt-BR', { 
              style: 'currency', 
              currency: 'BRL',
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })}
          </span>
        );
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (text) => {
        const statusMap = {
          'pending': { text: 'Pendente', color: 'default' },
          'filled': { text: 'Preenchida', color: 'blue' },
          'tp_hit': { text: 'TP Atingido', color: 'green' },
          'sl_hit': { text: 'SL Atingido', color: 'red' },
          'closed': { text: 'Fechada', color: 'default' }
        };
        const status = statusMap[text] || { text, color: 'default' };
        return <Tag color={status.color}>{status.text}</Tag>;
      }
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>Historico de Ordens</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadOrders}>
            Atualizar
          </Button>
          <Button icon={<DownloadOutlined />}>
            Exportar
          </Button>
        </Space>
      </div>

      <Card title="Filtros de Busca" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8} lg={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Periodo</div>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['Data Inicial', 'Data Final']}
              value={filters.dateRange}
              onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
              format="DD/MM/YYYY"
            />
          </Col>

          <Col xs={24} sm={12} md={8} lg={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Simbolo</div>
            <Select
              style={{ width: '100%' }}
              placeholder="Todos os simbolos"
              value={filters.symbol}
              onChange={(value) => setFilters({ ...filters, symbol: value })}
              allowClear
            >
              <Option value="WIN$">WIN$</Option>
              <Option value="WDO$">WDO$</Option>
              <Option value="PETR4">PETR4</Option>
              <Option value="VALE3">VALE3</Option>
            </Select>
          </Col>

          <Col xs={24} sm={12} md={8} lg={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Estrategia</div>
            <Select
              style={{ width: '100%' }}
              placeholder="Todas as estrategias"
              value={filters.strategy}
              onChange={(value) => setFilters({ ...filters, strategy: value })}
              allowClear
            >
              {strategies.map(s => (
                <Option key={s.name} value={s.name}>
                  {s.display_name || s.name}
                </Option>
              ))}
            </Select>
          </Col>

          <Col xs={24} sm={12} md={8} lg={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Status</div>
            <Select
              style={{ width: '100%' }}
              placeholder="Todos os status"
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              allowClear
            >
              <Option value="pending">Pendente</Option>
              <Option value="filled">Preenchida</Option>
              <Option value="tp_hit">TP Atingido</Option>
              <Option value="sl_hit">SL Atingido</Option>
              <Option value="closed">Fechada</Option>
            </Select>
          </Col>
        </Row>

        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleSearch}
              >
                Buscar
              </Button>
              <Button
                icon={<ClearOutlined />}
                onClick={handleClearFilters}
              >
                Limpar Filtros
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          dataSource={orders}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Total: ${total} ordens` }}
          locale={{ emptyText: 'Nenhuma ordem encontrada. Ajuste os filtros e clique em "Buscar".' }}
        />
      </Card>
    </div>
  );
}

export default History;

