import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Switch, Space, Typography, message, Tag } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { strategiesAPI } from '../services/api';

const { Title } = Typography;

function Strategies() {
  const [loading, setLoading] = useState(true);
  const [strategies, setStrategies] = useState([]);

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const response = await strategiesAPI.list();
      setStrategies(response.data || []);
    } catch (error) {
      console.error('Erro ao carregar estrategias:', error);
      message.error('Erro ao carregar estrategias');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (strategy, active) => {
    try {
      if (active) {
        await strategiesAPI.activate(strategy.name);
        message.success(`Estrategia ${strategy.display_name} ativada`);
      } else {
        await strategiesAPI.deactivate(strategy.name);
        message.success(`Estrategia ${strategy.display_name} desativada`);
      }
      loadStrategies();
    } catch (error) {
      console.error('Erro ao alternar estrategia:', error);
      message.error('Erro ao alterar estrategia');
    }
  };

  const columns = [
    {
      title: 'Nome',
      dataIndex: 'display_name',
      key: 'display_name',
      render: (text, record) => (
        <div>
          <div><strong>{text}</strong></div>
          <div style={{ fontSize: '12px', color: '#999' }}>{record.name}</div>
        </div>
      )
    },
    {
      title: 'Simbolo',
      dataIndex: 'symbol',
      key: 'symbol'
    },
    {
      title: 'Timeframe',
      dataIndex: 'timeframe',
      key: 'timeframe',
      render: (value) => `M${value}`
    },
    {
      title: 'Volume',
      dataIndex: 'volume',
      key: 'volume'
    },
    {
      title: 'Sinais',
      dataIndex: 'total_signals',
      key: 'total_signals'
    },
    {
      title: 'Ordens',
      dataIndex: 'total_orders',
      key: 'total_orders'
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => (
        <Tag color={record.is_active ? 'green' : 'default'}>
          {record.is_active ? 'Ativa' : 'Inativa'}
        </Tag>
      )
    },
    {
      title: 'Acao',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Switch
            checked={record.is_active}
            onChange={(checked) => handleToggleActive(record, checked)}
            checkedChildren="ON"
            unCheckedChildren="OFF"
          />
          <Button type="link" size="small">Editar</Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>Estrategias</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadStrategies}>
            Atualizar
          </Button>
          <Button type="primary" icon={<PlusOutlined />}>
            Nova Estrategia
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          dataSource={strategies}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'Nenhuma estrategia cadastrada' }}
        />
      </Card>
    </div>
  );
}

export default Strategies;

