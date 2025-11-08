import React, { useState, useEffect } from 'react';
import { Card, Form, InputNumber, Button, Select, message, Space, Typography, Spin, Alert, Input, Divider, Tooltip } from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined, QuestionCircleOutlined } from '@ant-design/icons';
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
      console.log('Tentando carregar estrategias de: http://localhost:8000/api/strategies/discover/available');
      const response = await axios.get('http://localhost:8000/api/strategies/discover/available');
      console.log('Resposta recebida:', response.data);
      const strategiesData = response.data.strategies || [];
      
      setStrategies(strategiesData);
      
      // Selecionar primeira estrategia por padrao
      if (strategiesData.length > 0) {
        selectStrategy(strategiesData[0]);
      } else {
        console.warn('Nenhuma estrategia encontrada na resposta');
      }
    } catch (error) {
      console.error('Erro DETALHADO ao carregar estrategias:', error);
      console.error('Erro response:', error.response);
      console.error('Erro message:', error.message);
      message.error(`Erro ao carregar lista de estrategias: ${error.message}`);
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

  // Dicionario de descricoes dos parametros
  const parameterDescriptions = {
    // Amplitude e Volume
    'min_amplitude_mult': 'Multiplicador da amplitude minima. Candles com amplitude maior que (media * este valor) sao considerados "elefantes"',
    'min_volume_mult': 'Multiplicador do volume minimo. Candles com volume maior que (media * este valor) sao considerados "elefantes"',
    'max_sombra_pct': 'Percentual maximo de sombra (pavio) permitido em relacao ao corpo do candle',
    'lookback_amplitude': 'Numero de candles anteriores para calcular a media de amplitude',
    'lookback_volume': 'Numero de candles anteriores para calcular a media de volume',
    
    // Horarios
    'horario_inicio': 'Hora de inicio das operacoes (formato 24h)',
    'minuto_inicio': 'Minuto de inicio das operacoes',
    'horario_fim': 'Hora limite para NOVAS entradas (formato 24h)',
    'minuto_fim': 'Minuto limite para novas entradas',
    'horario_fechamento': 'Hora de fechamento forcado de todas as posicoes',
    'minuto_fechamento': 'Minuto de fechamento forcado',
    
    // Stop Loss e Take Profit
    'sl_atr_mult': 'Multiplicador do ATR para calcular o Stop Loss. SL = preco_entrada +/- (ATR * este valor)',
    'tp_atr_mult': 'Multiplicador do ATR para calcular o Take Profit. TP = preco_entrada +/- (ATR * este valor)',
    
    // Gerais
    'atr_period': 'Periodo (numero de candles) para calcular o Average True Range (ATR)',
    'volume_bars': 'Numero de barras para calcular a media de volume',
    'enable_trailing_stop': 'Ativar trailing stop (stop loss que acompanha o preco a favor)',
    'trailing_stop_distance': 'Distancia em pontos para o trailing stop',
  };

  const renderParameterInput = (key, value) => {
    const label = key
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    
    const description = parameterDescriptions[key] || 'Parametro da estrategia';

    if (typeof value === 'number') {
      // Parametros numericos
      return (
        <Form.Item
          key={key}
          label={
            <Space>
              <span>{label}</span>
              <Tooltip title={description}>
                <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
              </Tooltip>
            </Space>
          }
          name={key}
          rules={[{ required: true, message: `${label} e obrigatorio` }]}
          help={<Text type="secondary" style={{ fontSize: 12 }}>{description}</Text>}
        >
          <InputNumber
            style={{ width: '100%' }}
            step={key.includes('ratio') || key.includes('mult') || key.includes('pct') ? 0.1 : 1}
            precision={key.includes('ratio') || key.includes('mult') || key.includes('pct') ? 1 : 0}
          />
        </Form.Item>
      );
    } else if (typeof value === 'boolean') {
      // Parametros booleanos
      return (
        <Form.Item
          key={key}
          label={
            <Space>
              <span>{label}</span>
              <Tooltip title={description}>
                <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
              </Tooltip>
            </Space>
          }
          name={key}
          valuePropName="checked"
          help={<Text type="secondary" style={{ fontSize: 12 }}>{description}</Text>}
        >
          <Select style={{ width: '100%' }}>
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
          label={
            <Space>
              <span>{label}</span>
              <Tooltip title={description}>
                <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
              </Tooltip>
            </Space>
          }
          name={key}
          rules={[{ required: true, message: `${label} e obrigatorio` }]}
          help={<Text type="secondary" style={{ fontSize: 12 }}>{description}</Text>}
        >
          <Input style={{ width: '100%' }} />
        </Form.Item>
      );
    }

    // Fallback generico
    return (
      <Form.Item
        key={key}
        label={
          <Space>
            <span>{label}</span>
            <Tooltip title={description}>
              <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
            </Tooltip>
          </Space>
        }
        name={key}
        help={<Text type="secondary" style={{ fontSize: 12 }}>{description}</Text>}
      >
        <Input style={{ width: '100%' }} />
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
            placeholder="Selecione uma estrategia..."
            showSearch
            filterOption={(input, option) =>
              option.children.toString().toLowerCase().includes(input.toLowerCase())
            }
          >
            {strategies.map(s => (
              <Option key={s.strategy_key} value={s.strategy_key}>
                <Space>
                  <SettingOutlined />
                  <span>
                    <strong>{s.name}</strong>
                    {s.metadata?.description && (
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                        - {s.metadata.description}
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
          title={`Parametros: ${selectedStrategy.name}`}
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
            {/* Parametros organizados em secoes */}
            <div style={{ maxWidth: 800 }}>
              <Divider orientation="left">Parametros de Deteccao</Divider>
              {Object.entries(parameters)
                .filter(([key]) => key.includes('amplitude') || key.includes('volume') || key.includes('sombra') || key.includes('lookback'))
                .map(([key, value]) => renderParameterInput(key, value))
              }

              <Divider orientation="left">Horarios de Operacao</Divider>
              {Object.entries(parameters)
                .filter(([key]) => key.includes('horario') || key.includes('minuto'))
                .map(([key, value]) => renderParameterInput(key, value))
              }

              <Divider orientation="left">Stop Loss e Take Profit</Divider>
              {Object.entries(parameters)
                .filter(([key]) => key.includes('sl_') || key.includes('tp_') || key.includes('atr'))
                .map(([key, value]) => renderParameterInput(key, value))
              }

              <Divider orientation="left">Outros Parametros</Divider>
              {Object.entries(parameters)
                .filter(([key]) => 
                  !key.includes('amplitude') && 
                  !key.includes('volume') && 
                  !key.includes('sombra') && 
                  !key.includes('lookback') &&
                  !key.includes('horario') && 
                  !key.includes('minuto') &&
                  !key.includes('sl_') && 
                  !key.includes('tp_') && 
                  !key.includes('atr')
                )
                .map(([key, value]) => renderParameterInput(key, value))
              }
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

