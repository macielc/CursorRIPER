import React, { useState, useEffect } from 'react';
import { Card, Table, DatePicker, Select, Space, Typography, Button, Tag, Row, Col, Dropdown, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, SearchOutlined, ClearOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import { ordersAPI, strategiesAPI } from '../services/api';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

function History() {
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState([
    // DADOS SIMULADOS PARA DEMONSTRACAO
    {
      id: 1,
      mt5_order_id: '123456',
      strategy_name: 'Barra Elefante',
      symbol: 'WIN$',
      action: 'buy',
      status: 'tp_hit',
      entry_price: 163450,
      exit_price: 163800,
      sl_price: 163200,
      tp_price: 163800,
      volume: 1.0,
      pnl_points: 350.00,
      pnl_currency: 875.00,
      created_at: '2025-11-08T10:15:00',
      filled_at: '2025-11-08T10:15:05',
      closed_at: '2025-11-08T10:45:30'
    },
    {
      id: 2,
      mt5_order_id: '123457',
      strategy_name: 'Barra Elefante',
      symbol: 'WIN$',
      action: 'sell',
      status: 'sl_hit',
      entry_price: 163200,
      exit_price: 163350,
      sl_price: 163350,
      tp_price: 162850,
      volume: 1.0,
      pnl_points: -150.00,
      pnl_currency: -375.00,
      created_at: '2025-11-08T11:30:00',
      filled_at: '2025-11-08T11:30:05',
      closed_at: '2025-11-08T11:42:15'
    }
  ]);
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
    // loadOrders(); // COMENTADO PARA MOSTRAR DADOS SIMULADOS
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

  const handleExport = (format) => {
    try {
      // Preparar parametros (mesmos dos filtros)
      const params = new URLSearchParams();
      params.append('format', format);
      
      if (filters.dateRange && filters.dateRange[0] && filters.dateRange[1]) {
        params.append('date_from', filters.dateRange[0].format('YYYY-MM-DD'));
        params.append('date_to', filters.dateRange[1].format('YYYY-MM-DD'));
      }
      
      if (filters.symbol) params.append('symbol', filters.symbol);
      if (filters.strategy) params.append('strategy_name', filters.strategy);
      if (filters.status) params.append('status', filters.status);
      
      // Criar URL e abrir em nova aba para download
      const url = `http://localhost:8000/api/orders/export?${params.toString()}`;
      window.open(url, '_blank');
      
      message.success(`Exportando ${orders.length} ordens para ${format.toUpperCase()}...`);
    } catch (error) {
      console.error('Erro ao exportar:', error);
      message.error('Erro ao exportar ordens');
    }
  };

  const exportMenuItems = [
    {
      key: 'csv',
      label: 'Exportar CSV',
      icon: <FileTextOutlined />,
      onClick: () => handleExport('csv')
    },
    {
      key: 'excel',
      label: 'Exportar Excel',
      icon: <FileExcelOutlined />,
      onClick: () => handleExport('excel')
    }
  ];

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
      render: (value, record) => {
        // Se a ordem ainda está aberta (não foi fechada)
        const isOpen = record.status === 'pending' || record.status === 'filled';
        
        if (isOpen || value === null || value === undefined) {
          return (
            <span style={{ 
              color: '#1890ff', // Azul
              fontWeight: 600,
              fontSize: '13px'
            }}>
              ORDEM ABERTA
            </span>
          );
        }
        
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
          <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
            <Button icon={<DownloadOutlined />}>
              Exportar
            </Button>
          </Dropdown>
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

