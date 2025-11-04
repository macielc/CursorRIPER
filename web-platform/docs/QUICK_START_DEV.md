# QUICK START - Desenvolvimento

Guia rapido para desenvolvedores continuarem a implementacao.

---

## SETUP INICIAL

### 1. Clonar/Navegar para o projeto

```powershell
cd C:\Users\AltF4\Documents\#__MACTESTER\release_1.0\web-platform
```

### 2. Backend Setup

```powershell
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Criar .env (se nao existir)
cp .env.example .env  # Criar este arquivo se necessario

# Inicializar banco
python -c "from app.core.database import init_db; init_db()"

# Rodar backend
python app/main.py
```

Backend rodando em: http://localhost:8000

### 3. Frontend Setup

```powershell
# Novo terminal
cd frontend

# Instalar dependencias
npm install

# Rodar dev server
npm run dev
```

Frontend rodando em: http://localhost:3000

---

## TESTAR API (Backend)

### Via curl

```powershell
# Health check
curl http://localhost:8000/health

# Listar estrategias
curl http://localhost:8000/api/strategies/

# Descobrir estrategias disponiveis
curl http://localhost:8000/api/strategies/discover/available

# Listar ordens
curl http://localhost:8000/api/orders/

# Stats de ordens
curl http://localhost:8000/api/orders/stats/summary
```

### Via Browser

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## IMPLEMENTAR FRONTEND

### Estrutura basica App.jsx

```jsx
// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import ptBR from 'antd/locale/pt_BR';

import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Monitor from './pages/Monitor';
import History from './pages/History';

function App() {
  return (
    <ConfigProvider locale={ptBR}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/monitor" element={<Monitor />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
```

### Criar API Service

```javascript
// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para tratar erros
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Strategies
export const strategiesAPI = {
  list: (params) => api.get('/strategies/', { params }),
  get: (name) => api.get(`/strategies/${name}`),
  create: (data) => api.post('/strategies/', data),
  update: (name, data) => api.put(`/strategies/${name}`, data),
  delete: (name) => api.delete(`/strategies/${name}`),
  activate: (name) => api.post(`/strategies/${name}/activate`),
  deactivate: (name) => api.post(`/strategies/${name}/deactivate`),
  discover: () => api.get('/strategies/discover/available')
};

// Orders
export const ordersAPI = {
  list: (params) => api.get('/orders/', { params }),
  get: (id) => api.get(`/orders/${id}`),
  stats: (params) => api.get('/orders/stats/summary', { params }),
  todaySummary: () => api.get('/orders/today/summary'),
  closeAll: () => api.post('/orders/close-all')
};

export default api;
```

### Exemplo pagina Dashboard

```jsx
// frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { ordersAPI } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [todayOrders, setTodayOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, todayRes] = await Promise.all([
        ordersAPI.stats(),
        ordersAPI.todaySummary()
      ]);
      
      setStats(statsRes.data);
      setTodayOrders(todayRes.data.orders || []);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>MacTester Dashboard</h1>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Trades Hoje"
              value={todayOrders.length}
              prefix={<ArrowUpOutlined />}
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
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="Profit Factor"
              value={stats?.profit_factor || 0}
              precision={2}
            />
          </Card>
        </Col>
      </Row>
      
      <Card title="Ordens Hoje">
        <Table
          dataSource={todayOrders}
          loading={loading}
          columns={[
            { title: 'Hora', dataIndex: 'created_at', key: 'time' },
            { title: 'Estrategia', dataIndex: 'strategy_name', key: 'strategy' },
            { title: 'Simbolo', dataIndex: 'symbol', key: 'symbol' },
            { title: 'Tipo', dataIndex: 'action', key: 'action' },
            { title: 'Preco', dataIndex: 'entry_price', key: 'price' },
            { title: 'Status', dataIndex: 'status', key: 'status' }
          ]}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}
```

---

## PROXIMAS TAREFAS

### Priority 1 - Fazer funcionar basico

1. [ ] Criar `frontend/src/main.jsx`
2. [ ] Criar `frontend/src/App.jsx`
3. [ ] Criar `frontend/src/pages/Dashboard.jsx`
4. [ ] Criar `frontend/src/services/api.js`
5. [ ] Testar frontend conectando com backend

### Priority 2 - Gestao de Estrategias

1. [ ] Criar `frontend/src/pages/Strategies.jsx`
2. [ ] Criar `frontend/src/components/StrategyCard.jsx`
3. [ ] Criar `frontend/src/components/StrategyEditor.jsx`
4. [ ] Implementar CRUD completo

### Priority 3 - Monitor Live

1. [ ] Criar `backend/app/api/routes/monitor.py`
2. [ ] Criar `backend/app/services/monitor_service.py`
3. [ ] Integrar com `live_trading/monitor.py`
4. [ ] WebSocket para eventos real-time

### Priority 4 - Integracao MT5

1. [ ] Criar `backend/app/services/mt5_service.py`
2. [ ] Implementar conexao MT5
3. [ ] Implementar envio de ordens
4. [ ] Implementar busca de dados

---

## ESTRUTURA DE ARQUIVOS ESPERADA

```
web-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── strategies.py  [OK]
│   │   │       ├── orders.py      [OK]
│   │   │       ├── monitor.py     [CRIAR]
│   │   │       ├── dashboard.py   [CRIAR]
│   │   │       └── mt5.py         [CRIAR]
│   │   ├── core/
│   │   │   ├── config.py          [OK]
│   │   │   └── database.py        [OK]
│   │   ├── models/                [OK]
│   │   ├── services/              [CRIAR]
│   │   └── main.py                [OK]
│   └── requirements.txt           [OK]
│
├── frontend/
│   ├── src/
│   │   ├── components/            [CRIAR]
│   │   ├── pages/                 [CRIAR]
│   │   ├── services/              [CRIAR]
│   │   ├── App.jsx                [CRIAR]
│   │   └── main.jsx               [CRIAR]
│   ├── package.json               [OK]
│   └── vite.config.js             [OK]
│
├── deploy/
│   ├── deploy.ps1                 [OK]
│   └── install_service.ps1        [OK]
│
└── docs/
    ├── IMPLEMENTATION_STATUS.md   [OK]
    └── QUICK_START_DEV.md         [OK]
```

---

## COMANDOS UTEIS

### Backend

```powershell
# Rodar backend
cd backend
python app/main.py

# Rodar com auto-reload
uvicorn app.main:app --reload

# Criar migracao
alembic revision --autogenerate -m "mensagem"

# Aplicar migracoes
alembic upgrade head

# Shell interativo
python -i
>>> from app.core.database import SessionLocal
>>> from app.models import Strategy
>>> db = SessionLocal()
>>> estrategias = db.query(Strategy).all()
```

### Frontend

```powershell
# Rodar dev
cd frontend
npm run dev

# Build producao
npm run build

# Preview build
npm run preview

# Lint
npm run lint
```

### Git

```powershell
# Status
git status

# Adicionar tudo
git add .

# Commit
git commit -m "Implementa Dashboard basico"

# Push
git push
```

---

## DEBUG

### Backend nao conecta MT5

1. Verificar se MT5 esta rodando
2. Verificar se `MetaTrader5` Python package esta instalado
3. Ver logs: `tail -f backend/logs/backend.log`

### Frontend nao carrega

1. Verificar se backend esta rodando
2. Verificar proxy no `vite.config.js`
3. Limpar cache: `rm -rf node_modules/.vite`

### WebSocket nao conecta

1. Verificar URL: `ws://localhost:8000/ws`
2. Verificar CORS no backend
3. Testar com: `wscat -c ws://localhost:8000/ws`

---

## RECURSOS

- Ant Design: https://ant.design/components/overview
- TradingView Charts: https://tradingview.github.io/lightweight-charts/
- FastAPI Docs: https://fastapi.tiangolo.com/
- React Router: https://reactrouter.com/

---

**Boa sorte com a implementacao!**

