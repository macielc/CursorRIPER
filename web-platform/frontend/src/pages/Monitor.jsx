import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Typography, Badge, Empty } from 'antd';

const { Title, Text } = Typography;

function Monitor() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    // TODO: Implementar WebSocket para receber updates em tempo real
    // const ws = new WebSocket('ws://localhost:8000/ws/monitor');
  }, []);

  return (
    <div>
      <Title level={2}>Monitor em Tempo Real</Title>

      <Row gutter={16}>
        <Col span={24}>
          <Card>
            <Empty
              description={
                <div>
                  <Text type="secondary">Monitor em tempo real</Text>
                  <br />
                  <Text type="secondary">Conecte uma sessao de live trading para ver dados em tempo real</Text>
                </div>
              }
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Sessoes Ativas">
            <Badge status="default" text="Nenhuma sessao ativa" />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Ultimos Sinais">
            <Empty description="Nenhum sinal detectado" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Monitor;

