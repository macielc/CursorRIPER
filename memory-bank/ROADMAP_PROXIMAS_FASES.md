# 🗺️ ROADMAP MacTester - Próximas Fases
**Versão**: 1.0  
**Data de criação**: 2025-11-04  
**Última atualização**: 2025-11-04  
**Status**: Deploy N150 completo ✅ - Aguardando continuidade

---

## 📊 CONTEXTO ATUAL (04/11/2025)

### ✅ O QUE FOI CONQUISTADO

**Sistema Híbrido FUNCIONANDO no N150**:
- ✅ Backend FastAPI rodando (porta 8000)
- ✅ Frontend React+Vite rodando (porta 3000/5173)
- ✅ Monitor Python integrado (PID 7408)
- ✅ WebSocket transmitindo logs em tempo real
- ✅ Interface web profissional (Ant Design)
- ✅ MT5 configurado (conta demo Clear)
- ✅ Modo Dry-Run seguro ativo
- ✅ Estratégia Barra Elefante implementada
- ✅ Python 3.11 venvs configurados (backend + live_trading)
- ✅ Sistema modular (monitor.py v2.0 genérico)

**Evidências**:
```
Status Monitor: PID 7408, Uptime: 0h 0m 3s, Memória: 3.8 MB
Logs em tempo real: ✅ "Monitor iniciado com sucesso (modo dry-run)"
Interface: http://localhost:3000/monitor
```

### ⏳ O QUE FALTA

**Gaps Principais**:
1. TradingView Charts (visualização de candles)
2. Identity Verification Python ↔ Rust (não validada)
3. Pipeline end-to-end (não testado)
4. Segunda estratégia (validar modularidade)
5. Alertas Telegram
6. Backups automáticos

**Completude Geral**: ~75% do projeto completo

---

## 🎯 FASE 1: MELHORIAS IMEDIATAS WEB PLATFORM

**Prioridade**: 🔴 **ALTA**  
**Tempo estimado**: 3-4 horas  
**Quando**: Primeira sessão após retorno (sábado)

---

### **1.1 - TradingView Lightweight Charts** ⭐

**Objetivo**: Adicionar gráficos profissionais de candles com marcadores de trades

**Por quê?**:
- Visual profissional e intuitivo
- Facilita análise de performance
- Mostra entrada/saída visualmente
- Complementa deploy bem-sucedido

**Implementação**:

#### **Frontend - Instalar biblioteca**:
```bash
cd web-platform/frontend
npm install lightweight-charts
```

#### **Criar componente** `src/components/TradingViewChart.jsx`:
```javascript
import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

function TradingViewChart({ data, markers }) {
  const chartContainerRef = useRef();
  const chartRef = useRef();

  useEffect(() => {
    // Criar chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
    });

    // Série de candles
    const candlestickSeries = chart.addCandlestickSeries();
    candlestickSeries.setData(data);

    // Adicionar marcadores (trades)
    candlestickSeries.setMarkers(markers);

    chartRef.current = chart;

    // Cleanup
    return () => chart.remove();
  }, [data, markers]);

  return <div ref={chartContainerRef} style={{ position: 'relative' }} />;
}

export default TradingViewChart;
```

#### **Backend - Endpoint para dados históricos**:
```python
# app/api/routes/charts.py (CRIAR NOVO)
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
import MetaTrader5 as mt5

router = APIRouter(prefix="/charts", tags=["charts"])

@router.get("/candles")
def get_candles(
    symbol: str = "WIN$",
    timeframe: int = 5,  # M5
    bars: int = 500
):
    """Retorna candles para o chart"""
    # Conectar MT5
    if not mt5.initialize():
        return {"error": "MT5 não inicializado"}
    
    # Buscar dados
    timeframe_mt5 = mt5.TIMEFRAME_M5 if timeframe == 5 else mt5.TIMEFRAME_M15
    rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, bars)
    
    # Converter para formato TradingView
    candles = []
    for rate in rates:
        candles.append({
            "time": int(rate['time']),
            "open": float(rate['open']),
            "high": float(rate['high']),
            "low": float(rate['low']),
            "close": float(rate['close']),
        })
    
    mt5.shutdown()
    return candles

@router.get("/markers")
def get_trade_markers(strategy: str = None):
    """Retorna marcadores de trades para o chart"""
    from app.models import Order
    from app.core.database import get_db
    
    db = next(get_db())
    query = db.query(Order)
    
    if strategy:
        query = query.filter(Order.strategy_name == strategy)
    
    orders = query.order_by(Order.created_at.desc()).limit(100).all()
    
    markers = []
    for order in orders:
        if order.filled_at:
            markers.append({
                "time": int(order.filled_at.timestamp()),
                "position": "belowBar" if order.action == "buy" else "aboveBar",
                "color": "#26a69a" if order.action == "buy" else "#ef5350",
                "shape": "arrowUp" if order.action == "buy" else "arrowDown",
                "text": f"{order.action.upper()} @ {order.entry_price}"
            })
    
    return markers
```

#### **Integrar no Dashboard**:
```javascript
// src/pages/Dashboard.jsx
import TradingViewChart from '../components/TradingViewChart';

function Dashboard() {
  const [candlesData, setCandlesData] = useState([]);
  const [markers, setMarkers] = useState([]);

  useEffect(() => {
    // Buscar candles
    api.get('/charts/candles?symbol=WIN$&bars=500')
      .then(res => setCandlesData(res.data));
    
    // Buscar marcadores
    api.get('/charts/markers')
      .then(res => setMarkers(res.data));
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      <Card title="Gráfico WIN$ - M5">
        <TradingViewChart data={candlesData} markers={markers} />
      </Card>
      {/* Resto do dashboard */}
    </div>
  );
}
```

#### **Registrar rota no backend**:
```python
# app/main.py
from app.api.routes import strategies, orders, monitor, charts  # Adicionar charts

app.include_router(charts.router, prefix="/api")
```

**Tempo estimado**: 3-4 horas

**Resultado esperado**: Dashboard com gráfico profissional mostrando candles + trades

---

### **1.2 - Página de Configuração de Parâmetros** 🔧

**Objetivo**: Interface para editar parâmetros das estratégias sem tocar em arquivos

**Implementação**:

#### **Frontend - Criar página** `src/pages/Settings.jsx`:
```javascript
import React, { useState, useEffect } from 'react';
import { Card, Form, InputNumber, Button, Select, message } from 'antd';
import api from '../services/api';

function Settings() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [parameters, setParameters] = useState({});
  const [form] = Form.useForm();

  useEffect(() => {
    // Buscar estratégias disponíveis
    api.get('/strategies/discover/available')
      .then(res => {
        setStrategies(res.data.strategies);
        if (res.data.strategies.length > 0) {
          selectStrategy(res.data.strategies[0].strategy_key);
        }
      });
  }, []);

  const selectStrategy = (key) => {
    const strategy = strategies.find(s => s.strategy_key === key);
    setSelectedStrategy(strategy);
    setParameters(strategy.parameters);
    form.setFieldsValue(strategy.parameters);
  };

  const handleSave = async (values) => {
    try {
      await api.post(`/strategies/${selectedStrategy.strategy_key}/parameters`, values);
      message.success('Parâmetros salvos com sucesso!');
    } catch (error) {
      message.error('Erro ao salvar parâmetros');
    }
  };

  return (
    <div>
      <h2>Configurações</h2>
      
      <Card title="Selecionar Estratégia">
        <Select
          style={{ width: 300 }}
          value={selectedStrategy?.strategy_key}
          onChange={selectStrategy}
        >
          {strategies.map(s => (
            <Select.Option key={s.strategy_key} value={s.strategy_key}>
              {s.display_name}
            </Select.Option>
          ))}
        </Select>
      </Card>

      {selectedStrategy && (
        <Card title={`Parâmetros: ${selectedStrategy.display_name}`} style={{ marginTop: 16 }}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            initialValues={parameters}
          >
            {Object.entries(parameters).map(([key, value]) => (
              <Form.Item
                key={key}
                label={key.replace(/_/g, ' ').toUpperCase()}
                name={key}
              >
                {typeof value === 'number' ? (
                  <InputNumber step={0.1} style={{ width: 200 }} />
                ) : (
                  <Input style={{ width: 200 }} />
                )}
              </Form.Item>
            ))}
            
            <Form.Item>
              <Button type="primary" htmlType="submit">
                Salvar Parâmetros
              </Button>
            </Form.Item>
          </Form>
        </Card>
      )}
    </div>
  );
}

export default Settings;
```

#### **Backend - Endpoint para salvar parâmetros**:
```python
# app/api/routes/strategies.py
import yaml
from pathlib import Path

@router.post("/{strategy_key}/parameters")
def update_strategy_parameters(strategy_key: str, parameters: dict):
    """Atualiza parâmetros de uma estratégia"""
    from app.core.config import settings
    
    config_file = settings.STRATEGIES_PATH / f"config_{strategy_key}.yaml"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Estratégia não encontrada")
    
    # Ler config atual
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Atualizar parâmetros
    config['parameters'] = parameters
    
    # Salvar
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    return {"success": True, "message": "Parâmetros atualizados"}
```

#### **Adicionar rota no App.jsx**:
```javascript
// src/App.jsx
import Settings from './pages/Settings';

<Route path="/settings" element={<Settings />} />
```

#### **Adicionar item no menu**:
```javascript
// src/components/Sidebar.jsx
<Menu.Item key="/settings" icon={<SettingOutlined />}>
  <Link to="/settings">Configurações</Link>
</Menu.Item>
```

**Tempo estimado**: 2-3 horas

**Resultado esperado**: Interface para ajustar parâmetros sem editar YAMLs

---

### **1.3 - Filtros Avançados no Histórico** 🔍

**Objetivo**: Busca refinada de ordens passadas

**Implementação**:

#### **Frontend - Melhorar** `src/pages/History.jsx`:
```javascript
import { DatePicker, Select, Input, Space } from 'antd';
const { RangePicker } = DatePicker;

function History() {
  const [filters, setFilters] = useState({
    dateRange: null,
    symbol: null,
    strategy: null,
    status: null,
  });

  const fetchOrders = () => {
    const params = {};
    if (filters.dateRange) {
      params.start_date = filters.dateRange[0].format('YYYY-MM-DD');
      params.end_date = filters.dateRange[1].format('YYYY-MM-DD');
    }
    if (filters.symbol) params.symbol = filters.symbol;
    if (filters.strategy) params.strategy = filters.strategy;
    if (filters.status) params.status = filters.status;

    api.get('/orders', { params })
      .then(res => setOrders(res.data));
  };

  return (
    <Card title="Histórico de Ordens">
      <Space style={{ marginBottom: 16 }}>
        <RangePicker onChange={dates => setFilters({...filters, dateRange: dates})} />
        <Select
          placeholder="Símbolo"
          style={{ width: 120 }}
          onChange={val => setFilters({...filters, symbol: val})}
          allowClear
        >
          <Select.Option value="WIN$">WIN$</Select.Option>
          <Select.Option value="WDO$">WDO$</Select.Option>
        </Select>
        <Select
          placeholder="Estratégia"
          style={{ width: 150 }}
          onChange={val => setFilters({...filters, strategy: val})}
          allowClear
        >
          <Select.Option value="barra_elefante">Barra Elefante</Select.Option>
        </Select>
        <Button type="primary" onClick={fetchOrders}>Buscar</Button>
      </Space>
      
      <Table dataSource={orders} columns={columns} />
    </Card>
  );
}
```

#### **Backend - Melhorar endpoint** `/api/orders`:
```python
# app/api/routes/orders.py
@router.get("/")
def get_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Buscar ordens com filtros"""
    query = db.query(Order)
    
    if start_date:
        query = query.filter(Order.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Order.created_at <= datetime.fromisoformat(end_date))
    if symbol:
        query = query.filter(Order.symbol == symbol)
    if strategy:
        query = query.filter(Order.strategy_name == strategy)
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return orders
```

**Tempo estimado**: 1-2 horas

---

### **1.4 - Export CSV/Excel** 📊

**Objetivo**: Download de dados para análise externa

**Implementação**:

#### **Backend - Endpoint de export**:
```python
# app/api/routes/orders.py
from fastapi.responses import StreamingResponse
import pandas as pd
import io

@router.get("/export")
def export_orders(
    format: str = "csv",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Exportar ordens para CSV/Excel"""
    query = db.query(Order)
    
    if start_date:
        query = query.filter(Order.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Order.created_at <= datetime.fromisoformat(end_date))
    
    orders = query.all()
    
    # Converter para DataFrame
    df = pd.DataFrame([{
        'id': o.id,
        'timestamp': o.created_at,
        'strategy': o.strategy_name,
        'symbol': o.symbol,
        'action': o.action,
        'price': o.entry_price,
        'sl': o.sl_price,
        'tp': o.tp_price,
        'volume': o.volume,
        'pnl_pts': o.pnl_points,
        'pnl_currency': o.pnl_currency,
        'status': o.status
    } for o in orders])
    
    # Gerar arquivo
    buffer = io.BytesIO()
    if format == "csv":
        df.to_csv(buffer, index=False)
        media_type = "text/csv"
        filename = f"orders_{datetime.now().strftime('%Y%m%d')}.csv"
    else:  # excel
        df.to_excel(buffer, index=False)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"orders_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

#### **Frontend - Botão de export**:
```javascript
// src/pages/History.jsx
<Button
  icon={<DownloadOutlined />}
  onClick={() => {
    window.open('/api/orders/export?format=csv', '_blank');
  }}
>
  Exportar CSV
</Button>
```

**Tempo estimado**: 1 hora

**Resultado esperado**: Download de CSV/Excel com todos os dados

---

## 🧪 FASE 2: VALIDAÇÃO ENGINES

**Prioridade**: 🟡 **MÉDIA-ALTA**  
**Tempo estimado**: 2-3 dias  
**Objetivo**: Garantir Python ↔ Rust 100% idênticos

---

### **2.1 - Smoke Test Python** 🐍

**Objetivo**: Validar Python em período curto (1 dia)

**Comando**:
```bash
cd engines/python

python mactester.py optimize \
  --strategy barra_elefante \
  --tests 100 \
  --timeframe 5m \
  --period "2024-01-02" "2024-01-02" \
  --output ../../results/backtests/python/smoke_test_jan02.json
```

**Parâmetros**:
- 100 combinações de parâmetros
- 1 dia (2 de janeiro de 2024)
- M5 (timeframe 5 minutos)
- Output JSON para comparação

**Critérios de sucesso**:
- ✅ Executa sem erros
- ✅ Gera trades (esperado: 0-3 trades em 1 dia)
- ✅ Arquivo JSON criado
- ✅ Tempo de execução razoável (<10 min)

**Output esperado**:
```json
{
  "strategy": "barra_elefante",
  "period": "2024-01-02",
  "tests_run": 100,
  "best_params": { ... },
  "trades": [
    {
      "timestamp": "2024-01-02 10:15:00",
      "action": "buy",
      "price": 163450,
      "sl": 163200,
      "tp": 163800,
      "pnl_points": 350
    }
  ],
  "metrics": {
    "total_trades": 2,
    "win_rate": 0.50,
    "sharpe_ratio": 0.85,
    "max_drawdown": -200
  }
}
```

**Tempo estimado**: 30 min (executar + analisar)

---

### **2.2 - Smoke Test Rust** 🦀

**Objetivo**: Validar Rust com EXATAMENTE os mesmos parâmetros

**Comando**:
```bash
cd engines/rust

.\optimize_batches.exe \
  --strategy barra_elefante \
  --tests 100 \
  --period 2024-01-02 2024-01-02 \
  --timeframe 5 \
  --output ..\..\results\backtests\rust\smoke_test_jan02.json
```

**IMPORTANTE**: Usar EXATAMENTE os mesmos:
- Número de testes (100)
- Período (2024-01-02)
- Timeframe (5)
- Seed aleatório (se aplicável)

**Critérios de sucesso**:
- ✅ Executa sem erros
- ✅ Mesmo número de trades que Python
- ✅ Trades nos mesmos timestamps
- ✅ Preços idênticos (±1 ponto tolerância)
- ✅ Mais rápido que Python (expectativa: 10-50x)

**Tempo estimado**: 30 min

---

### **2.3 - Comparação Trade-by-Trade** ⚖️

**Objetivo**: Verificar 100% identidade Python ↔ Rust

**Criar script** `pipeline/comparar_engines.py`:
```python
"""
Compara resultados Python vs Rust trade-by-trade
"""
import json
import sys
from datetime import datetime

def load_results(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def compare_trades(python_trades, rust_trades, tolerance=1.0):
    """
    Compara trades com tolerância de 1 ponto
    """
    discrepancies = []
    
    if len(python_trades) != len(rust_trades):
        return False, f"Número de trades diferente: Python={len(python_trades)}, Rust={len(rust_trades)}"
    
    for i, (pt, rt) in enumerate(zip(python_trades, rust_trades)):
        # Comparar timestamps (±1 candle tolerância = ±5 min em M5)
        time_diff = abs((datetime.fromisoformat(pt['timestamp']) - 
                        datetime.fromisoformat(rt['timestamp'])).total_seconds())
        if time_diff > 300:  # 5 minutos
            discrepancies.append(f"Trade {i}: Timestamp diff = {time_diff}s")
        
        # Comparar preços
        if abs(pt['price'] - rt['price']) > tolerance:
            discrepancies.append(f"Trade {i}: Price diff = {abs(pt['price'] - rt['price'])}")
        
        # Comparar SL/TP
        if abs(pt['sl'] - rt['sl']) > tolerance:
            discrepancies.append(f"Trade {i}: SL diff = {abs(pt['sl'] - rt['sl'])}")
        if abs(pt['tp'] - rt['tp']) > tolerance:
            discrepancies.append(f"Trade {i}: TP diff = {abs(pt['tp'] - rt['tp'])}")
        
        # Comparar PnL
        if abs(pt.get('pnl_points', 0) - rt.get('pnl_points', 0)) > tolerance:
            discrepancies.append(f"Trade {i}: PnL diff = {abs(pt['pnl_points'] - rt['pnl_points'])}")
    
    if discrepancies:
        return False, "\n".join(discrepancies)
    
    return True, "✅ IDENTIDADE 100% VERIFICADA!"

def main():
    if len(sys.argv) < 3:
        print("Uso: python comparar_engines.py <python_results.json> <rust_results.json>")
        sys.exit(1)
    
    python_file = sys.argv[1]
    rust_file = sys.argv[2]
    
    print("Carregando resultados...")
    python_results = load_results(python_file)
    rust_results = load_results(rust_file)
    
    print(f"Python: {len(python_results['trades'])} trades")
    print(f"Rust: {len(rust_results['trades'])} trades")
    
    identical, message = compare_trades(
        python_results['trades'],
        rust_results['trades']
    )
    
    print("\n" + "="*60)
    if identical:
        print("✅ SUCESSO: Engines são idênticas!")
        print(message)
        sys.exit(0)
    else:
        print("❌ ERRO: Discrepâncias encontradas!")
        print(message)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Executar**:
```bash
cd pipeline

python comparar_engines.py \
  ../results/backtests/python/smoke_test_jan02.json \
  ../results/backtests/rust/smoke_test_jan02.json
```

**Critérios de aprovação**:
- ✅ Número de trades idêntico
- ✅ Timestamps dentro de ±1 candle (5 min)
- ✅ Preços entrada/saída dentro de ±1 pt
- ✅ PnL idêntico (±1 pt)

**Se houver discrepâncias**: Investigar código Rust vs Python

**Tempo estimado**: 1-2 horas (incluindo análise)

---

### **2.4 - Documentar Discrepâncias** 📝

**Se houver diferenças**, investigar:

**Possíveis causas**:
1. **Arredondamento de floats**: Python vs Rust precisão
2. **Ordem de operações**: Cálculos em ordem diferente
3. **Timezone**: Timestamps em fusos diferentes
4. **Indicadores**: ATR, médias calculadas diferente
5. **Seed aleatório**: Otimizador com seeds diferentes

**Criar documento** `results/comparison/python_vs_rust/discrepancy_report.md`:
```markdown
# Relatório de Discrepâncias Python vs Rust

## Resumo
- Data: 2024-01-02
- Trades Python: X
- Trades Rust: Y
- Discrepâncias: Z

## Discrepâncias Identificadas

### 1. Trade #5 - Timestamp diferente
- Python: 2024-01-02 10:15:00
- Rust: 2024-01-02 10:20:00
- Diferença: 5 minutos
- Causa: TBD

### 2. Trade #10 - Preço entrada diferente
- Python: 163450
- Rust: 163451
- Diferença: 1 ponto
- Causa: Arredondamento de float

## Ações Corretivas
1. [ ] Corrigir timezone handling no Rust
2. [ ] Padronizar arredondamento
3. [ ] Re-testar após correções
```

**Tempo estimado**: 2-4 horas (dependendo da quantidade)

---

### **2.5 - Benchmark Performance** 🚀

**Objetivo**: Medir velocidade Rust vs Python

**Teste 1: Pequeno** (1 dia, 100 combos):
```bash
# Python
time python mactester.py optimize --strategy barra_elefante --tests 100 --period "2024-01-02" "2024-01-02"

# Rust
time .\optimize_batches.exe --strategy barra_elefante --tests 100 --period 2024-01-02 2024-01-02
```

**Teste 2: Médio** (1 semana, 1000 combos):
```bash
# Python
time python mactester.py optimize --tests 1000 --period "2024-01-02" "2024-01-08"

# Rust
time .\optimize_batches.exe --tests 1000 --period 2024-01-02 2024-01-08
```

**Expectativa**:
- Rust deve ser **10-50x mais rápido**
- Exemplo: Python 10 min → Rust 30 segundos

**Documentar** em `results/comparison/performance_benchmark.md`:
```markdown
# Benchmark Performance Python vs Rust

## Teste 1: Smoke Test (100 combos, 1 dia)
- Python: 2min 15s
- Rust: 8s
- Speedup: **17x**

## Teste 2: Médio (1000 combos, 1 semana)
- Python: 18min 30s
- Rust: 45s
- Speedup: **24.6x**

## Conclusão
Rust confirmado 10-50x mais rápido.
Viável para Mass Optimization (10k+ combos).
```

**Tempo estimado**: 1 hora

---

## 🔬 FASE 3: PIPELINE COMPLETO

**Prioridade**: 🟡 **MÉDIA**  
**Tempo estimado**: 1 semana  
**Objetivo**: Validar Barra Elefante completamente

---

### **3.1 - Testar Orquestrador** 🎭

**Objetivo**: Validar que `run_pipeline.py` funciona end-to-end

**Comando**:
```bash
cd pipeline

python run_pipeline.py \
  --strategy barra_elefante \
  --motor python \
  --period "2024-01-02" "2024-01-02" \
  --tests 100
```

**O que deve acontecer**:
1. Fase 1: Smoke Test (100 combos)
2. Fase 2: Mass Optimization (skip ou pequeno)
3. Fase 3: Walk-Forward
4. Fase 4: Out-of-Sample
5. Fase 5: Outlier Analysis
6. Fase 6: Final Report

**Critérios de sucesso**:
- ✅ Executa todas as 6 fases sem crash
- ✅ Gera arquivos de output para cada fase
- ✅ Relatório final é gerado
- ✅ Logs são gravados

**Se falhar**: Debugar fase por fase

**Tempo estimado**: 2-3 horas (incluindo debug)

---

### **3.2 - Fase 1-2: Optimization** 🔍

**Objetivo**: Smoke Test + Mass Optimization em janeiro/2024

**Configuração**:
```bash
python run_pipeline.py \
  --strategy barra_elefante \
  --motor rust \
  --period "2024-01-01" "2024-01-31" \
  --tests 5000 \
  --phases smoke,mass_optimization
```

**Parâmetros**:
- **Motor**: Rust (velocidade)
- **Período**: Janeiro 2024 (1 mês)
- **Combinações**: 5.000
- **Fases**: 1 e 2 apenas

**Output esperado**:
```
results/validation/barra_elefante_jan2024/
├── phase1_smoke_test.json
├── phase2_mass_optimization.json
├── best_params_top10.csv
└── optimization_summary.md
```

**Tempo de execução**: ~2-4 horas (Rust)

**Análise**:
- Identificar top 10 combinações de parâmetros
- Verificar métricas (Sharpe, Win Rate, Drawdown)
- Selecionar "candidatos" para validação

**Tempo estimado**: 4-6 horas (exec + análise)

---

### **3.3 - Fase 3-6: Validation** ✅

**Objetivo**: Validar robustez dos melhores parâmetros

**Fase 3: Walk-Forward**
```bash
python pipeline/validators/fase3_walkforward.py \
  --params results/validation/barra_elefante_jan2024/best_params_top10.csv \
  --period "2024-02-01" "2024-03-31" \
  --windows 6
```

- 6 janelas deslizantes (2 meses)
- Treino: 3 semanas, Teste: 1 semana
- Critério: 60%+ janelas positivas

**Fase 4: Out-of-Sample**
```bash
python pipeline/validators/fase4_out_of_sample.py \
  --params best_params_top3.csv \
  --period "2024-04-01" "2024-04-30" \
  --min_trades 5
```

- Período nunca visto (abril 2024)
- Critério: Min 5 trades, Sharpe > 0.5

**Fase 5: Outlier Analysis**
```bash
python pipeline/validators/fase5_outlier_analysis.py \
  --results fase4_results.json \
  --method zscore \
  --threshold 2.5
```

- Remove outliers (Z-score > 2.5)
- Recalcula métricas
- Critério: Sharpe > 0.7 sem outliers

**Fase 6: Final Report**
```bash
python pipeline/validators/fase6_relatorio_final.py \
  --all_results results/validation/barra_elefante_jan2024/ \
  --output final_report.pdf
```

- Consolida todas as fases
- Gera relatório PDF completo
- **Decisão**: APPROVED ou REJECTED

**Tempo estimado**: 2-3 dias (incluindo análise)

---

### **3.4 - Análise de Resultados** 📊

**Objetivo**: Interpretar relatórios e decidir próximos passos

**Documentos a revisar**:
1. `best_params_top10.csv` - Melhores parâmetros
2. `equity_curves.png` - Gráficos de equity
3. `metrics_summary.md` - Métricas consolidadas
4. `final_report.pdf` - Relatório executivo

**Análise**:
```markdown
# Análise Pipeline - Barra Elefante

## Métricas Consolidadas
- Total trades (jan-abr 2024): 87
- Win rate: 32%
- Sharpe ratio: 0.85
- Max drawdown: -1,200 pts
- Recovery factor: 2.1

## Walk-Forward (6 janelas)
- Janelas positivas: 4/6 (67%) ✅
- Consistência: APROVADO

## Out-of-Sample (abril)
- Trades: 18
- Sharpe: 0.62 ✅
- Performance: APROVADO

## Outlier Analysis
- Outliers removidos: 3 trades
- Sharpe sem outliers: 0.78 ✅
- Robustez: APROVADO

## DECISÃO FINAL
✅ **APPROVED** - Estratégia validada para live trading
```

**Tempo estimado**: 4-6 horas

---

### **3.5 - Go/No-Go Decision** 🚦

**Se APPROVED** ✅:
→ Seguir para Fase 4 (Live Trading Avançado)
→ Implementar alertas, backups, etc.
→ Preparar para demo extendida

**Se REJECTED** ❌:
→ Analisar por que falhou
→ Opções:
  1. Ajustar parâmetros e re-testar
  2. Modificar lógica da estratégia
  3. Criar nova estratégia
  4. Descartar e focar em outra

**Documentar decisão** em `results/validation/barra_elefante_jan2024/GO_NOGO_DECISION.md`

**Tempo estimado**: 1-2 horas (discussão + documentação)

---

## 🚀 FASE 4: LIVE TRADING AVANÇADO

**Prioridade**: 🟢 **MÉDIA-BAIXA**  
**Tempo estimado**: 3-5 dias  
**Pré-requisito**: Fase 3 APPROVED

---

### **4.1 - Alertas Telegram** 📱

**Objetivo**: Notificações em tempo real de eventos importantes

**Setup**:

1. **Criar bot Telegram**:
   - Falar com @BotFather
   - Copiar token
   - Adicionar ao `.env` do backend

2. **Implementar serviço** `app/services/telegram_notifier.py`:
```python
"""
Serviço de notificações Telegram
"""
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from app.core.config import settings

class TelegramNotifier:
    def __init__(self):
        if settings.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            self.chat_id = settings.TELEGRAM_CHAT_ID
        else:
            self.bot = None
    
    async def send_message(self, message: str):
        if not self.bot:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except TelegramError as e:
            print(f"Erro ao enviar Telegram: {e}")
    
    async def signal_detected(self, signal: dict):
        message = f"""
🎯 *SINAL DETECTADO*

Estratégia: {signal['strategy']}
Ação: {signal['action'].upper()}
Preço: {signal['price']}
SL: {signal['sl']}
TP: {signal['tp']}
Razão: {signal['reason']}
        """
        await self.send_message(message)
    
    async def order_filled(self, order: dict):
        message = f"""
✅ *ORDEM EXECUTADA*

#{order['id']} - {order['action'].upper()}
Preço: {order['entry_price']}
Volume: {order['volume']}
Ticket MT5: {order['mt5_order_id']}
        """
        await self.send_message(message)
    
    async def order_rejected(self, order: dict, reason: str):
        message = f"""
❌ *ORDEM REJEITADA*

Ação: {order['action'].upper()}
Preço: {order['price']}
Razão: {reason}
        """
        await self.send_message(message)
    
    async def kill_switch_activated(self, reason: str):
        message = f"""
🛑 *KILL SWITCH ATIVADO*

⚠️ Monitor foi pausado!
Razão: {reason}

Verifique o sistema imediatamente.
        """
        await self.send_message(message)

# Singleton
_notifier = None

def get_telegram_notifier():
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier
```

3. **Integrar com MonitorService**:
```python
# app/services/monitor_service.py
from app.services.telegram_notifier import get_telegram_notifier
import asyncio

# No método start():
notifier = get_telegram_notifier()
asyncio.create_task(notifier.send_message("🚀 Monitor iniciado"))

# Ao detectar sinal (via WebSocket callback):
asyncio.create_task(notifier.signal_detected(signal_data))
```

**Eventos a notificar**:
- 🎯 Sinal detectado
- ✅ Ordem executada
- ❌ Ordem rejeitada
- 🛑 Kill switch ativado
- ⚠️ Erro crítico no monitor
- 📊 Resumo diário (final do dia)

**Tempo estimado**: 3-4 horas

---

### **4.2 - Sistema de Backup Automático** 💾

**Objetivo**: Proteção de dados críticos

**Implementar** `app/services/backup_service.py`:
```python
"""
Serviço de backup automático
"""
import shutil
import schedule
import time
from pathlib import Path
from datetime import datetime, timedelta
from app.core.config import settings

class BackupService:
    def __init__(self):
        self.backup_dir = settings.BACKUP_DIR
        self.retention_days = settings.BACKUP_RETENTION_DAYS
    
    def backup_database(self):
        """Backup do SQLite"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source = Path("mactester.db")
        dest = self.backup_dir / f"mactester_{timestamp}.db"
        
        if source.exists():
            shutil.copy2(source, dest)
            print(f"✅ Backup DB: {dest}")
            self.cleanup_old_backups()
    
    def backup_configs(self):
        """Backup dos YAMLs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / f"configs_{timestamp}"
        backup_folder.mkdir(parents=True, exist_ok=True)
        
        # Copiar config.yaml principal
        shutil.copy2("../../live_trading/config.yaml", backup_folder)
        
        # Copiar YAMLs das estratégias
        strategies_path = Path("../../live_trading/strategies")
        for yaml_file in strategies_path.glob("config_*.yaml"):
            shutil.copy2(yaml_file, backup_folder)
        
        print(f"✅ Backup configs: {backup_folder}")
    
    def cleanup_old_backups(self):
        """Remove backups antigos"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                print(f"🗑️ Removido backup antigo: {backup_file}")
    
    def start_scheduled_backups(self):
        """Inicia backups agendados"""
        # Backup DB a cada trade (trigger via evento)
        # Backup configs diário às 00:00
        schedule.every().day.at("00:00").do(self.backup_configs)
        
        print("📅 Backups agendados iniciados")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check a cada minuto

# Singleton
_backup_service = None

def get_backup_service():
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service
```

**Integrar no startup** `app/main.py`:
```python
import threading
from app.services.backup_service import get_backup_service

@app.on_event("startup")
async def startup_event():
    # ... (código existente)
    
    # Iniciar backups em thread separada
    backup_service = get_backup_service()
    backup_thread = threading.Thread(target=backup_service.start_scheduled_backups, daemon=True)
    backup_thread.start()
    logger.info("Backup service iniciado")
```

**Rotação de logs**:
```python
# app/core/logging_config.py
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/backend.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=30  # 30 arquivos
)
```

**Tempo estimado**: 2-3 horas

---

### **4.3 - Segunda Estratégia** 🎯

**Objetivo**: Validar modularidade do sistema

**Opções de estratégia**:

1. **Inside Bar** (reversão):
   - Detecta inside bars (candle dentro do anterior)
   - Entrada no rompimento
   - Stop na extrema oposta
   - Target: 2x o risco

2. **Power Breakout** (momentum):
   - Detecta breakout de máxima/mínima de X barras
   - Volume acima da média
   - Entrada na confirmação
   - Trailing stop

3. **Mean Reversion** (retorno à média):
   - Detecta afastamento de média móvel
   - RSI sobrecomprado/sobrevendido
   - Entrada na reversão
   - Target: retorno à média

**Processo de implementação**:

1. **Criar estrutura**:
```bash
mkdir strategies/inside_bar
touch strategies/inside_bar/__init__.py
touch strategies/inside_bar/strategy.py
```

2. **Implementar lógica** `strategies/inside_bar/strategy.py`:
```python
"""
Inside Bar Strategy
"""
import pandas as pd
from typing import Dict, Optional

class InsideBarStrategy:
    def __init__(self, params: Dict):
        self.name = "Inside Bar"
        self.lookback = params.get('lookback', 1)
        self.volume_mult = params.get('volume_mult', 1.2)
        self.sl_atr_mult = params.get('sl_atr_mult', 2.0)
        self.tp_atr_mult = params.get('tp_atr_mult', 3.0)
    
    def detect(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Detecta inside bar e retorna sinal
        """
        if len(df) < self.lookback + 2:
            return None
        
        # Barra atual e anterior
        current = df.iloc[-1]
        mother = df.iloc[-2]
        
        # Inside bar: high < mother.high AND low > mother.low
        is_inside = (current['high'] < mother['high'] and 
                     current['low'] > mother['low'])
        
        if not is_inside:
            return None
        
        # Volume acima da média
        volume_avg = df['volume'].rolling(20).mean().iloc[-1]
        if current['volume'] < volume_avg * self.volume_mult:
            return None
        
        # Determinar direção: close > mother.close = bullish
        is_bullish = current['close'] > mother['close']
        
        # Calcular SL/TP baseado em ATR
        atr = df['atr'].iloc[-1]
        
        if is_bullish:
            entry = mother['high'] + 5  # Breakout acima
            sl = mother['low'] - self.sl_atr_mult * atr
            tp = entry + self.tp_atr_mult * atr
            
            return {
                'action': 'buy',
                'price': entry,
                'sl': sl,
                'tp': tp,
                'reason': f'Inside Bar Bullish (mother high={mother["high"]})'
            }
        else:
            entry = mother['low'] - 5  # Breakout abaixo
            sl = mother['high'] + self.sl_atr_mult * atr
            tp = entry - self.tp_atr_mult * atr
            
            return {
                'action': 'sell',
                'price': entry,
                'sl': sl,
                'tp': tp,
                'reason': f'Inside Bar Bearish (mother low={mother["low"]})'
            }
```

3. **Criar config YAML** `live_trading/strategies/config_inside_bar.yaml`:
```yaml
strategy_name: "Inside Bar"
strategy_class: "InsideBarStrategy"
strategy_module: "strategies.inside_bar.strategy"

parameters:
  lookback: 1
  volume_mult: 1.2
  sl_atr_mult: 2.0
  tp_atr_mult: 3.0
  horario_inicio: 9
  minuto_inicio: 15
  horario_fim: 17
  minuto_fim: 0

metadata:
  description: "Estratégia de reversão baseada em inside bars"
  author: "MacTester Team"
  version: "1.0"
  created_at: "2025-11-04"
```

4. **Testar**:
```bash
cd live_trading
python monitor.py --strategy inside_bar --dry-run
```

5. **Validar via pipeline** (Fase 3):
```bash
cd pipeline
python run_pipeline.py --strategy inside_bar --period "2024-01-01" "2024-01-31"
```

6. **Se aprovada**, rodar em paralelo:
```bash
# Terminal 1
python monitor.py --strategy barra_elefante

# Terminal 2
python monitor.py --strategy inside_bar
```

**Tempo estimado**: 1-2 dias (impl + validação)

---

### **4.4 - Multi-Instância** 🔀

**Objetivo**: Rodar múltiplas estratégias simultaneamente

**Já suportado pelo sistema!**

**Setup**:
```bash
# Terminal 1 - Elefante WIN$
cd live_trading
python monitor.py --strategy barra_elefante --symbol WIN$

# Terminal 2 - Inside Bar WIN$
python monitor.py --strategy inside_bar --symbol WIN$

# Terminal 3 - Elefante WDO$
python monitor.py --strategy barra_elefante --symbol WDO$
```

**Cuidados**:
- Cada instância usa margem independente
- Total de margin usage = soma de todas
- Verificar que conta tem margem suficiente
- Configurar `max_positions` por estratégia

**Monitoramento**:
- Interface web mostra todas as estratégias
- Filtrar por estratégia no histórico
- Dashboard agregado

**Tempo estimado**: 1 hora (teste e validação)

---

### **4.5 - Validação Demo Estendida** 🧪

**Objetivo**: Rodar 1 semana em conta demo com modo real

**Setup**:

1. **Confirmar conta demo Clear ativa** ✅ (já tem)

2. **Configurar modo REAL** (mas em demo):
```yaml
# live_trading/config.yaml
monitor:
  dry_run: false  # ATIVAR MODO REAL
  check_interval: 5
  
risk:
  max_daily_loss_points: 500
  max_consecutive_losses: 3
  max_positions: 1

trading:
  symbol: "WIN$"
  volume: 1.0
```

3. **Iniciar monitor**:
```bash
python monitor.py --strategy barra_elefante
```

4. **Monitorar ativamente**:
- ✅ Verificar execuções a cada 30 min
- ✅ Anotar slippage (diferença entrada esperada vs real)
- ✅ Verificar fill rate (ordens executadas vs rejeitadas)
- ✅ Comparar com backtest

5. **Registrar métricas diárias**:
```markdown
# Validação Demo - Semana 1

## Segunda-feira (06/11)
- Sinais detectados: 2
- Ordens executadas: 2
- Slippage médio: +3 pts
- PnL: +150 pts
- Observações: Execução ok, sem problemas

## Terça-feira (07/11)
- Sinais detectados: 1
- Ordens executadas: 0 (fora de horário)
- Observações: Sistema respeitou horários

...
```

6. **Análise final**:
```markdown
# Resumo Semana Demo

## Métricas
- Total sinais: 8
- Total ordens: 6
- Fill rate: 75%
- Slippage médio: +5 pts
- PnL: +320 pts (vs backtest +280 pts)
- Desvio: +14%

## Conclusão
✅ Performance próxima ao backtest
✅ Sistema estável
✅ Slippage aceitável
→ APROVADO para conta real (quando capitalizada)
```

**Tempo estimado**: 1 semana (monitoramento passivo + 2h análise)

---

## 💰 FASE 5: PRODUÇÃO (LONGO PRAZO)

**Prioridade**: 🔵 **BAIXA**  
**Tempo estimado**: Semanas/meses  
**Status**: Futuro distante

---

### **5.1 - Capitalização** 💵

**Situação atual**:
- Conta: GenialInvestimentos-PRD (REAL)
- Saldo: R$ 312,00
- Margem WIN$: ~R$ 2.500-3.000/contrato
- **Status**: ❌ **INSUFICIENTE**

**Requisito mínimo**: R$ 5.000  
**Recomendado**: R$ 10.000+

**Por quê?**:
- Margem WIN$ + buffer para drawdown
- Múltiplas posições (se necessário)
- Suportar sequência de losses

**Ações**:
1. Aumentar capital para R$ 5k-10k
2. OU operar ativo com margem menor (mini-contratos)
3. OU manter em demo até capitalizar

**Decisão pendente do usuário**

---

### **5.2 - Demo Extendida (2-4 semanas)** 🕐

**Após Fase 4.5** (1 semana demo):

Se resultados forem positivos:
→ Estender para 2-4 semanas adicionais

**Objetivo**:
- Validar estabilidade de longo prazo
- Testar diferentes condições de mercado
- Identificar edge cases

**Monitoramento**:
- Performance semanal
- Drawdown máximo observado
- Estabilidade do sistema (crashes, bugs)
- Análise de TODOS os trades

**Critérios para ir para real**:
- ✅ >80% uptime (sistema estável)
- ✅ Performance aceitável (positiva ou breakeven)
- ✅ Drawdown dentro do esperado
- ✅ Slippage controlado

**Tempo estimado**: 2-4 semanas (monitoramento passivo)

---

### **5.3 - Go/No-Go Real** 🚦

**Checklist CRÍTICO para conta REAL**:

- [ ] **Capital suficiente**: R$ 5.000+ depositado
- [ ] **Demo extendida bem-sucedida**: >2 semanas sem problemas
- [ ] **Performance aceitável**: Positiva ou no mínimo breakeven
- [ ] **Sistema estável**: Sem crashes, bugs corrigidos
- [ ] **Monitoramento ativo**: Possibilidade de verificar diariamente
- [ ] **Risco aceitável**: Capital que pode perder (trading é risco!)
- [ ] **Psicológico pronto**: Aceita drawdowns e volatilidade
- [ ] **Kill switches configurados**: max_daily_loss, max_consecutive_losses
- [ ] **Alertas ativos**: Telegram funcionando
- [ ] **Backups funcionando**: DB e configs protegidos

**Se TODOS os itens ✅**:
→ Ativar modo real na conta real

**Se qualquer item ❌**:
→ Continuar em demo até resolver

**Documentar decisão** em `PRODUCTION_GO_NOGO.md`

---

### **5.4 - Monitoramento 24/7** 👁️

**Em produção (conta real)**:

**Monitoramento diário**:
- [ ] Verificar interface web (status, ordens)
- [ ] Revisar logs (erros, warnings)
- [ ] Conferir saldo/margem no MT5
- [ ] Analisar trades do dia
- [ ] Responder alertas Telegram

**Monitoramento semanal**:
- [ ] Análise de performance (PnL, Sharpe, Drawdown)
- [ ] Comparar com backtest (desvios?)
- [ ] Revisar parâmetros (ajustar se necessário)
- [ ] Backup manual adicional

**Monitoramento mensal**:
- [ ] Relatório completo de performance
- [ ] Análise de edge cases
- [ ] Otimização de parâmetros (se aplicável)
- [ ] Go/No-Go para mês seguinte

**Ferramentas**:
- ✅ Dashboard web (já implementado)
- ✅ Alertas Telegram (Fase 4.1)
- ✅ Logs centralizados
- ✅ Métricas em tempo real

**Tempo estimado**: Contínuo (manutenção)

---

## 📊 PRIORIZAÇÃO E CRONOGRAMA

### **🔴 AGORA (Esta semana - Sábado após retorno)**

**Sessão 1** (3-4 horas):
1. ✅ **Fase 1.1** - TradingView Charts (3-4h)

**Sessão 2** (2-3 horas):
2. ✅ **Fase 1.2** - Página Configuração (2-3h)

**Total Fase 1**: ~6-7 horas

---

### **🟡 PRÓXIMO (Semana seguinte)**

**Dias 1-2** (8h/dia):
3. ✅ **Fase 2** - Validação Engines (2-3 dias)

**Dia 3** (2h):
4. ✅ **Fase 1.3-1.4** - Filtros + Export (2h)

**Total Semana 2**: ~18 horas

---

### **🟢 MÉDIO PRAZO (Próximo mês)**

**Semana 1-2**:
5. ✅ **Fase 3** - Pipeline Completo (1 semana)

**Semana 3-4**:
6. ✅ **Fase 4** - Live Trading Avançado (3-5 dias)

**Total Mês 1**: ~40 horas

---

### **🔵 LONGO PRAZO (3-6 meses)**

**Quando capitalizado**:
7. ✅ **Fase 5** - Produção (contínuo)

---

## 🎯 RECOMENDAÇÃO DE INÍCIO

**Primeira sessão após retorno (sábado)**:

```
INICIAR COM: FASE 1.1 - TradingView Lightweight Charts
```

**Por quê?**:
- ✅ Visual profissional e impactante
- ✅ Facilita análise de trades
- ✅ Complementa deploy bem-sucedido no N150
- ✅ Relativamente rápido (3-4 horas)
- ✅ Alto impacto na experiência do usuário
- ✅ Motivador para continuar

**Depois**:
```
FASE 1.2 - Página de Configuração de Parâmetros
```

**E então**:
```
FASE 2 - Validação Engines (Python vs Rust)
```

---

## 📋 CHECKLIST DE RETORNO

**Ao retornar no sábado**:

1. [ ] Abrir este arquivo: `memory-bank/ROADMAP_PROXIMAS_FASES.md`
2. [ ] Verificar status do N150 (servidores rodando?)
3. [ ] Acessar interface web: `http://localhost:3000`
4. [ ] Verificar monitor está rodando (PID, logs)
5. [ ] Escolher fase para começar (recomendação: 1.1)
6. [ ] Entrar no modo **Ω₄·EXECUTE**
7. [ ] Executar tarefas da fase escolhida

---

## 📝 RESUMO EXECUTIVO

| Fase | Prioridade | Tempo | Status | Quando |
|------|-----------|-------|--------|--------|
| **Fase 1: Web Platform** | 🔴 ALTA | 6-7h | 🟡 80% completo | Esta semana |
| **Fase 2: Engines** | 🟡 MÉDIA-ALTA | 2-3 dias | 🔴 Pendente | Próxima semana |
| **Fase 3: Pipeline** | 🟡 MÉDIA | 1 semana | 🔴 Pendente | Próximo mês |
| **Fase 4: Live Avançado** | 🟢 MÉDIA-BAIXA | 3-5 dias | 🔴 Pendente | Mês 1-2 |
| **Fase 5: Produção** | 🔵 BAIXA | Contínuo | 🔴 Futuro | 3-6 meses |

**Progresso atual**: ~75% do projeto completo  
**Deploy N150**: ✅ **FUNCIONANDO**  
**Sistema híbrido**: ✅ **VALIDADO**  
**Próximo milestone**: Completar Web Platform (Fase 1)

---

## 🏆 CONQUISTAS ATÉ AGORA

✅ **Sistema Híbrido Implementado**  
✅ **Deploy N150 Completo**  
✅ **Interface Web Profissional**  
✅ **Monitor Genérico v2.0**  
✅ **Python 3.11 Configurado**  
✅ **Modo Dry-Run Seguro**  
✅ **WebSocket Real-time**  
✅ **MT5 Demo Configurado**  

**Falta**: Melhorias visuais, validações, alertas, segunda estratégia

---

## 🎯 OBJETIVO FINAL

**Live Trading Automatizado ROBUSTO e VALIDADO**:
- Interface web completa com charts
- Múltiplas estratégias validadas
- Sistema estável 24/7
- Alertas e monitoramento
- Performance próxima ao backtest
- Preparado para conta real (quando capitalizada)

---

**BOA VIAGEM!** 🌴

**Nos vemos no sábado para continuar!** 🚀

---

**Arquivo**: `memory-bank/ROADMAP_PROXIMAS_FASES.md`  
**Criado em**: 2025-11-04  
**Próxima sessão**: Sábado (após retorno de viagem)  
**Modo de continuidade**: Ω₄·EXECUTE (Fase 1.1 - TradingView Charts)

