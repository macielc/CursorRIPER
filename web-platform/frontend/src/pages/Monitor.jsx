import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Typography, Badge, Button, Space, Alert, Tag, List } from 'antd';
import { PlayCircleOutlined, StopOutlined, ReloadOutlined, SyncOutlined } from '@ant-design/icons';
import api from '../services/api';

const { Title, Text } = Typography;

function Monitor() {
  const [status, setStatus] = useState({
    running: false,
    pid: null,
    uptime_seconds: null,
    memory_mb: null,
    cpu_percent: null
  });
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  // Scroll automatico para o final dos logs
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  // Conectar WebSocket
  useEffect(() => {
    connectWebSocket();
    fetchStatus();

    // Polling de status a cada 5s (backup caso WS falhe)
    const interval = setInterval(fetchStatus, 5000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      console.log('WebSocket conectado');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'monitor_log') {
        setLogs(prev => [...prev, message.data].slice(-100)); // Manter ultimos 100
      } else if (message.type === 'monitor_status') {
        setStatus(message.data);
      } else if (message.type === 'monitor_stopped') {
        setStatus({ running: false, pid: null, uptime_seconds: null, memory_mb: null });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket desconectado');
      setWsConnected(false);
      
      // Tentar reconectar apos 5s
      setTimeout(() => {
        if (wsRef.current === null || wsRef.current.readyState === WebSocket.CLOSED) {
          connectWebSocket();
        }
      }, 5000);
    };

    wsRef.current = ws;
  };

  const fetchStatus = async () => {
    try {
      const response = await api.get('/monitor/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Erro ao buscar status:', error);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      await api.post('/monitor/start', {
        dry_run: true  // Sempre iniciar em dry-run por seguranca
      });
      
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: 'Monitor iniciado com sucesso (modo dry-run)'
      }]);

      setTimeout(fetchStatus, 1000);
    } catch (error) {
      console.error('Erro ao iniciar monitor:', error);
      alert('Erro ao iniciar monitor: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await api.post('/monitor/stop');
      
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: 'Monitor parado'
      }]);

      setTimeout(fetchStatus, 1000);
    } catch (error) {
      console.error('Erro ao parar monitor:', error);
      alert('Erro ao parar monitor: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    setLoading(true);
    try {
      await api.post('/monitor/restart');
      setLogs([]);
      setTimeout(fetchStatus, 1000);
    } catch (error) {
      console.error('Erro ao reiniciar monitor:', error);
      alert('Erro ao reiniciar monitor: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const formatUptime = (seconds) => {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const getLogLevelColor = (level) => {
    switch(level) {
      case 'ERROR': return 'red';
      case 'WARNING': return 'orange';
      case 'INFO': return 'blue';
      case 'DEBUG': return 'default';
      default: return 'default';
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2}>Monitor em Tempo Real</Title>
        
        <Space>
          <Badge status={wsConnected ? 'success' : 'error'} text={wsConnected ? 'WS Conectado' : 'WS Desconectado'} />
        </Space>
      </div>

      {/* Status e Controles */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card 
            title="Status do Monitor" 
            extra={
              status.running ? 
                <Badge status="processing" text="Rodando" /> : 
                <Badge status="default" text="Parado" />
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text type="secondary">PID: </Text>
                <Text strong>{status.pid || '-'}</Text>
              </div>
              <div>
                <Text type="secondary">Uptime: </Text>
                <Text strong>{formatUptime(status.uptime_seconds)}</Text>
              </div>
              <div>
                <Text type="secondary">Memoria: </Text>
                <Text strong>{status.memory_mb ? `${status.memory_mb.toFixed(1)} MB` : '-'}</Text>
              </div>
              <div>
                <Text type="secondary">CPU: </Text>
                <Text strong>{status.cpu_percent ? `${status.cpu_percent.toFixed(1)}%` : '-'}</Text>
              </div>
            </Space>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Controles">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Alert
                message="Modo Dry-Run ativo"
                description="O monitor esta configurado para simulacao. Nenhuma ordem real sera executada."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Space>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleStart}
                  disabled={status.running || loading}
                  loading={loading && !status.running}
                >
                  Iniciar
                </Button>

                <Button
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStop}
                  disabled={!status.running || loading}
                  loading={loading && status.running}
                >
                  Parar
                </Button>

                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleRestart}
                  disabled={!status.running || loading}
                >
                  Reiniciar
                </Button>

                <Button
                  icon={<SyncOutlined />}
                  onClick={fetchStatus}
                  disabled={loading}
                >
                  Atualizar Status
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Logs em Tempo Real */}
      <Row gutter={16}>
        <Col span={24}>
          <Card title="Logs em Tempo Real" extra={<Text type="secondary">{logs.length} entradas</Text>}>
            <div 
              style={{ 
                height: '400px', 
                overflowY: 'auto', 
                backgroundColor: '#1e1e1e',
                padding: '12px',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '12px'
              }}
            >
              {logs.length === 0 ? (
                <Text type="secondary" style={{ color: '#888' }}>
                  Aguardando logs do monitor...
                </Text>
              ) : (
                logs.map((log, index) => (
                  <div key={index} style={{ marginBottom: '4px' }}>
                    <Tag color={getLogLevelColor(log.level)} style={{ marginRight: 8 }}>
                      {log.level}
                    </Tag>
                    <Text style={{ color: '#ccc' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </Text>
                    <Text style={{ color: '#fff', marginLeft: 8 }}>
                      {log.message}
                    </Text>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Monitor;
