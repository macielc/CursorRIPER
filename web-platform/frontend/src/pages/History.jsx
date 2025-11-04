import React, { useState, useEffect } from 'react';
import { Card, Table, DatePicker, Select, Space, Typography, Button, Tag } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { ordersAPI } from '../services/api';

const { Title } = Typography;
const { RangePicker } = DatePicker;

function History() {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [filters, setFilters] = useState({
    start_date: null,
    end_date: null,
    status: null
  });

  useEffect(() => {
    loadOrders();
  }, [filters]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const response = await ordersAPI.list(filters);
      setOrders(response.data || []);
    } catch (error) {
      console.error('Erro ao carregar historico:', error);
    } finally {
      setLoading(false);
    }
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
      title: 'PnL',
      dataIndex: 'pnl_points',
      key: 'pnl_points',
      render: (value) => {
        if (value === null || value === undefined) return '-';
        const color = value > 0 ? 'green' : value < 0 ? 'red' : 'default';
        return <span style={{ color }}>{value.toFixed(2)}</span>;
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

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <RangePicker
            placeholder={['Data Inicial', 'Data Final']}
            onChange={(dates) => {
              setFilters({
                ...filters,
                start_date: dates?.[0]?.format('YYYY-MM-DD'),
                end_date: dates?.[1]?.format('YYYY-MM-DD')
              });
            }}
          />
          <Select
            placeholder="Status"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Select.Option value="filled">Preenchida</Select.Option>
            <Select.Option value="tp_hit">TP Atingido</Select.Option>
            <Select.Option value="sl_hit">SL Atingido</Select.Option>
            <Select.Option value="closed">Fechada</Select.Option>
          </Select>
        </Space>

        <Table
          dataSource={orders}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: 'Nenhuma ordem encontrada' }}
        />
      </Card>
    </div>
  );
}

export default History;

