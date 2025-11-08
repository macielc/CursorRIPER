import React, { useState, useEffect } from 'react';
import { Card, Form, InputNumber, Button, Select, message, Space, Typography, Spin, Alert, Input, Divider } from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;

function Settings() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [parameters, setParameters] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/strategies/discover/available');
      const strategiesData = response.data.strategies || [];
      
      setStrategies(strategiesData);
      
      // Selecionar primeira estrategia por padrao
      if (strategiesData.length > 0) {
        selectStrategy(strategiesData[0]);
      }
    } catch (error) {
      console.error('Erro ao carregar estrategias:', error);
      message.error('Erro ao carregar lista de estrategias');
    } finally {
      setLoading(false);
    }
  };

  const selectStrategy = (strategy) => {
    setSelectedStrategy(strategy);
    setParameters(strategy.parameters || {});
    form.setFieldsValue(strategy.parameters || {});
  };

  const handleStrategyChange = (strategyKey) => {
    const strategy = strategies.find(s => s.strategy_key === strategyKey);
    if (strategy) {
      selectStrategy(strategy);
    }
  };

  const handleSave = async (values) => {
    if (!selectedStrategy) {
      message.warning('Selecione uma estrategia primeiro');
      return;
    }

    try {
      setSaving(true);
      
      await axios.post(
        `http://localhost:8000/api/strategies/${selectedStrategy.strategy_key}/parameters`,
        values
      );
      
      message.success('Parametros salvos com sucesso!');
      
      // Recarregar estrategias para pegar valores atualizados
      await loadStrategies();
      
    } catch (error) {
      console.error('Erro ao salvar parametros:', error);
      message.error('Erro ao salvar parametros. Verifique os valores e tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (selectedStrategy) {
      form.setFieldsValue(selectedStrategy.parameters || {});
      message.info('Valores redefinidos para os originais');
    }
  };

  const renderParameterInput = (key, value) => {
    const label = key
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    if (typeof value === 'number') {
      // Parametros numericos
      return (
        <Form.Item
          key={key}
          label={label}
          name={key}
          rules={[{ required: true, message: `${label} e obrigatorio` }]}
        >
          <InputNumber
            style={{ width: 200 }}
            step={key.includes('ratio') || key.includes('mult') ? 0.1 : 1}
            precision={key.includes('ratio') || key.includes('mult') ? 1 : 0}
          />
        </Form.Item>
      );
    } else if (typeof value === 'boolean') {
      // Parametros booleanos
      return (
        <Form.Item
          key={key}
          label={label}
          name={key}
          valuePropName="checked"
        >
          <Select style={{ width: 200 }}>
            <Option value={true}>Sim</Option>
            <Option value={false}>Nao</Option>
          </Select>
        </Form.Item>
      );
    } else if (typeof value === 'string') {
      // Parametros string
      return (
        <Form.Item
          key={key}
          label={label}
          name={key}
          rules={[{ required: true, message: `${label} e obrigatorio` }]}
        >
          <Input style={{ width: 200 }} />
        </Form.Item>
      );
    }

    // Fallback generico
    return (
      <Form.Item
        key={key}
        label={label}
        name={key}
      >
        <Input style={{ width: 200 }} />
      </Form.Item>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Carregando configuracoes..." />
      </div>
    );
  }

  if (strategies.length === 0) {
    return (
      <div>
        <Title level={2}>Configuracoes</Title>
        <Alert
          message="Nenhuma estrategia encontrada"
          description="Certifique-se de que existem arquivos config_*.yaml no diretorio live_trading/strategies/"
          type="warning"
          showIcon
        />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>
        <SettingOutlined /> Configuracoes
      </Title>
      
      <Card title="Selecionar Estrategia" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary">
            Escolha a estrategia que deseja configurar:
          </Text>
          
          <Select
            style={{ width: '100%', maxWidth: 400 }}
            value={selectedStrategy?.strategy_key}
            onChange={handleStrategyChange}
            size="large"
          >
            {strategies.map(s => (
              <Option key={s.strategy_key} value={s.strategy_key}>
                <Space>
                  <SettingOutlined />
                  <span>
                    <strong>{s.display_name}</strong>
                    {s.description && (
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                        - {s.description}
                      </Text>
                    )}
                  </span>
                </Space>
              </Option>
            ))}
          </Select>

          {selectedStrategy && (
            <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <Text strong>Arquivo: </Text>
              <Text code>{selectedStrategy.config_file}</Text>
              <br />
              {selectedStrategy.metadata?.version && (
                <>
                  <Text strong>Versao: </Text>
                  <Text>{selectedStrategy.metadata.version}</Text>
                  <br />
                </>
              )}
              {selectedStrategy.metadata?.author && (
                <>
                  <Text strong>Autor: </Text>
                  <Text>{selectedStrategy.metadata.author}</Text>
                </>
              )}
            </div>
          )}
        </Space>
      </Card>

      {selectedStrategy && (
        <Card 
          title={`Parametros: ${selectedStrategy.display_name}`}
          extra={
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadStrategies}
            >
              Recarregar
            </Button>
          }
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            initialValues={parameters}
          >
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '16px' 
            }}>
              {Object.entries(parameters).map(([key, value]) => 
                renderParameterInput(key, value)
              )}
            </div>

            <Divider />

            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SaveOutlined />}
                  loading={saving}
                  size="large"
                >
                  Salvar Parametros
                </Button>
                
                <Button 
                  onClick={handleReset}
                  disabled={saving}
                >
                  Resetar Valores
                </Button>
              </Space>
            </Form.Item>
          </Form>

          <Alert
            message="Atencao"
            description="Apos salvar os parametros, reinicie o monitor para que as mudancas tenham efeito."
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </Card>
      )}
    </div>
  );
}

export default Settings;

