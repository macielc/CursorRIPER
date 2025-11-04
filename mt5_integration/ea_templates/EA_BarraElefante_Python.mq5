//+------------------------------------------------------------------+
//| EA_BarraElefante_Python.mq5                                       |
//| MESMAS CONFIGURACOES DO PYTHON - Para Strategy Tester            |
//+------------------------------------------------------------------+
#property copyright "MacTester"
#property version   "1.00"
#property strict

//--- PARAMETROS IDENTICOS AO PYTHON
input double InpMinAmplitudeMult = 1.35;    // Min Amplitude Mult (PYTHON: min_amplitude_mult)
input double InpMinVolumeMult    = 1.3;     // Min Volume Mult (PYTHON: min_volume_mult)
input double InpMaxSombraPct     = 0.30;    // Max Sombra % (PYTHON: max_sombra_pct, corpo min 70%)
input int    InpLookbackAmplitude = 25;     // Lookback Amplitude (PYTHON: lookback_amplitude)
input int    InpLookbackVolume    = 20;     // Lookback Volume (PYTHON: 20 default)
input int    InpHoraInicio        = 9;      // Hora Inicio (PYTHON: horario_inicio)
input int    InpMinutoInicio      = 15;     // Minuto Inicio (PYTHON: minuto_inicio)
input int    InpHoraFim           = 11;     // Hora Fim (PYTHON: horario_fim)
input int    InpMinutoFim         = 0;      // Minuto Fim (PYTHON: minuto_fim)

// SL/TP - Mesmos do backtest Python
input double InpSL_ATR_Mult      = 2.0;     // SL ATR Mult (PYTHON: sl_atr_mult)
input double InpTP_ATR_Mult      = 3.0;     // TP ATR Mult (PYTHON: tp_atr_mult)
input int    InpHoraFechamento   = 12;      // Hora Fechamento Intraday (PYTHON: 12h15)
input int    InpMinutoFechamento = 15;      // Minuto Fechamento (PYTHON: 12h15)

input double InpLotSize          = 1.0;     // Tamanho do Lote
input int    InpMagicNumber      = 123456;  // Magic Number

//--- Globais
datetime barraElefante = 0;  // Timestamp da barra elefante
double maximaElefante = 0;
double minimaElefante = 0;
string direcaoElefante = "";
bool aguardandoSlippage = false;  // PYTHON: Slippage de 1 barra
ENUM_ORDER_TYPE tipoSlippage;

int totalTrades = 0;
int totalWins = 0;
int totalLosses = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   Print("========================================");
   Print("EA BARRA ELEFANTE - CONFIG PYTHON");
   Print("========================================");
   Print("Parametros:");
   Print("  Min Amp Mult: ", InpMinAmplitudeMult);
   Print("  Min Vol Mult: ", InpMinVolumeMult);
   Print("  Max Sombra: ", InpMaxSombraPct*100, "% (corpo min ", (1-InpMaxSombraPct)*100, "%)");
   Print("  Lookback Amp: ", InpLookbackAmplitude);
   Print("  Lookback Vol: ", InpLookbackVolume);
   Print("  Horario: ", InpHoraInicio, ":", InpMinutoInicio, " - ", InpHoraFim, ":", InpMinutoFim);
   Print("  SL: ", InpSL_ATR_Mult, " x ATR");
   Print("  TP: ", InpTP_ATR_Mult, " x ATR");
   Print("  Fechamento: ", InpHoraFechamento, ":", InpMinutoFechamento);
   Print("========================================");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("========================================");
   Print("EA FINALIZADO");
   Print("Total Trades: ", totalTrades);
   Print("  Wins: ", totalWins);
   Print("  Losses: ", totalLosses);
   if(totalTrades > 0)
      Print("  Win Rate: ", DoubleToString(totalWins*100.0/totalTrades, 2), "%");
   Print("========================================");
}

//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBar = 0;
   datetime currentBar = iTime(_Symbol, PERIOD_M5, 0);
   
   if(currentBar == lastBar)
      return;
   
   lastBar = currentBar;
   
   // PYTHON SLIPPAGE: Se tem ordem pendente (slippage de 1 barra), executar AGORA
   if(aguardandoSlippage && !PositionSelect(_Symbol))
   {
      AbrirPosicao(tipoSlippage);
      aguardandoSlippage = false;
      return;
   }
   
   // Se tem posicao, verificar saida
   if(PositionSelect(_Symbol))
   {
      VerificarSaida();
      return;
   }
   
   // PYTHON LOGIC: Se detectou elefante na barra anterior, verificar rompimento AGORA
   if(barraElefante > 0)
   {
      datetime barraAnterior = iTime(_Symbol, PERIOD_M5, 1);
      
      // Se elefante foi detectado na barra anterior (i-1), verificar rompimento agora (i)
      if(barraElefante == barraAnterior)
      {
         VerificarRompimento();
         // CRITICO: Limpar elefante depois de verificar (mesmo que nao rompa)
         barraElefante = 0;
         return;
      }
      else
      {
         // Elefante expirou (passou mais de 1 barra)
         barraElefante = 0;
      }
   }
   
   // Detectar novo elefante
   DetectarElefante();
}

//+------------------------------------------------------------------+
void DetectarElefante()
{
   MqlRates rates[];
   if(CopyRates(_Symbol, PERIOD_M5, 1, 1, rates) <= 0)
      return;
   
   MqlDateTime dt;
   TimeToStruct(rates[0].time, dt);
   
   // Filtro horario
   if(dt.hour < InpHoraInicio || (dt.hour == InpHoraInicio && dt.min < InpMinutoInicio))
      return;
   
   if(dt.hour > InpHoraFim || (dt.hour == InpHoraFim && dt.min > InpMinutoFim))
      return;
   
   // Calcular medias
   double ampMedia = CalcularAmplitudeMedia();
   double volMedia = CalcularVolumeMedia();
   
   if(ampMedia == 0 || volMedia == 0)
      return;
   
   // Filtros
   double amplitude = rates[0].high - rates[0].low;
   double corpo = MathAbs(rates[0].close - rates[0].open);
   
   if(amplitude < ampMedia * InpMinAmplitudeMult)
      return;
   
   if(rates[0].real_volume < volMedia * InpMinVolumeMult)
      return;
   
   if(amplitude == 0)
      return;
   
   double pctCorpo = corpo / amplitude;
   double limiteCorpo = 1.0 - InpMaxSombraPct;
   
   if(pctCorpo < limiteCorpo)
      return;
   
   // ELEFANTE DETECTADO!
   if(rates[0].close > rates[0].open)
   {
      direcaoElefante = "ALTA";
      maximaElefante = rates[0].high;
   }
   else
   {
      direcaoElefante = "BAIXA";
      minimaElefante = rates[0].low;
   }
   
   // PYTHON LOGIC: Armazenar timestamp da barra elefante
   barraElefante = rates[0].time;
}

//+------------------------------------------------------------------+
void VerificarRompimento()
{
   MqlRates rates[];
   if(CopyRates(_Symbol, PERIOD_M5, 0, 1, rates) <= 0)
      return;
   
   bool rompeu = false;
   ENUM_ORDER_TYPE tipo;
   
   if(direcaoElefante == "ALTA")
   {
      if(rates[0].high > maximaElefante)
      {
         rompeu = true;
         tipo = ORDER_TYPE_BUY;
      }
   }
   else
   {
      if(rates[0].low < minimaElefante)
      {
         rompeu = true;
         tipo = ORDER_TYPE_SELL;
      }
   }
   
   if(rompeu)
   {
      // PYTHON SLIPPAGE: Nao abre agora, aguarda 1 barra (entra no OPEN da proxima)
      aguardandoSlippage = true;
      tipoSlippage = tipo;
   }
   
   // PYTHON LOGIC: Limpar elefante (rompeu ou nao, esquece)
   barraElefante = 0;
}

//+------------------------------------------------------------------+
void AbrirPosicao(ENUM_ORDER_TYPE tipo)
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   
   // Calcular ATR
   double atr = CalcularATR(14);
   
   // Preco de entrada
   double preco = (tipo == ORDER_TYPE_BUY) ? tick.ask : tick.bid;
   
   // SL e TP
   double sl, tp;
   
   if(tipo == ORDER_TYPE_BUY)
   {
      sl = preco - (atr * InpSL_ATR_Mult);
      tp = preco + (atr * InpTP_ATR_Mult);
   }
   else
   {
      sl = preco + (atr * InpSL_ATR_Mult);
      tp = preco - (atr * InpTP_ATR_Mult);
   }
   
   // Normalizar
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   sl = NormalizeDouble(MathRound(sl/tickSize)*tickSize, _Digits);
   tp = NormalizeDouble(MathRound(tp/tickSize)*tickSize, _Digits);
   preco = NormalizeDouble(preco, _Digits);
   
   // Enviar ordem
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = InpLotSize;
   request.type = tipo;
   request.price = preco;
   request.sl = sl;
   request.tp = tp;
   request.deviation = 10;
   request.magic = InpMagicNumber;
   request.comment = "BarraElefante";
   
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         totalTrades++;
         Print("Trade #", totalTrades, " aberto: ", EnumToString(tipo), " @ ", preco, " SL:", sl, " TP:", tp);
      }
   }
}

//+------------------------------------------------------------------+
void VerificarSaida()
{
   if(!PositionSelect(_Symbol))
      return;
   
   // Fechamento intraday (12h15 - PYTHON)
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   if(dt.hour > InpHoraFechamento || (dt.hour == InpHoraFechamento && dt.min >= InpMinutoFechamento))
   {
      FecharPosicao("INTRADAY_CLOSE");
   }
}

//+------------------------------------------------------------------+
void FecharPosicao(string razao)
{
   if(!PositionSelect(_Symbol))
      return;
   
   double preco_entrada = PositionGetDouble(POSITION_PRICE_OPEN);
   double preco_atual = PositionGetDouble(POSITION_PRICE_CURRENT);
   double pnl = PositionGetDouble(POSITION_PROFIT);
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = PositionGetDouble(POSITION_VOLUME);
   request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price = (request.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   request.deviation = 10;
   request.magic = InpMagicNumber;
   
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         if(pnl > 0)
            totalWins++;
         else
            totalLosses++;
         
         Print("Trade fechado: PnL=", pnl, " Razao:", razao);
      }
   }
}

//+------------------------------------------------------------------+
double CalcularAmplitudeMedia()
{
   MqlRates rates[];
   if(CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackAmplitude, rates) <= 0)
      return 0;
   
   double soma = 0;
   for(int i = 0; i < InpLookbackAmplitude; i++)
      soma += (rates[i].high - rates[i].low);
   
   return soma / InpLookbackAmplitude;
}

//+------------------------------------------------------------------+
double CalcularVolumeMedia()
{
   MqlRates rates[];
   if(CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackVolume, rates) <= 0)
      return 0;
   
   double soma = 0;
   for(int i = 0; i < InpLookbackVolume; i++)
      soma += (double)rates[i].real_volume;
   
   return soma / InpLookbackVolume;
}

//+------------------------------------------------------------------+
double CalcularATR(int periodo)
{
   MqlRates rates[];
   if(CopyRates(_Symbol, PERIOD_M5, 0, periodo+1, rates) <= 0)
      return 100; // Fallback
   
   double soma = 0;
   for(int i = 1; i <= periodo; i++)
   {
      double high = rates[i].high;
      double low = rates[i].low;
      double close_prev = rates[i-1].close;
      
      double tr = MathMax(high - low, 
                  MathMax(MathAbs(high - close_prev), 
                         MathAbs(low - close_prev)));
      soma += tr;
   }
   
   return soma / periodo;
}
//+------------------------------------------------------------------+

