//+------------------------------------------------------------------+
//| EA_BarraElefante_CORRIGIDO.mq5                                    |
//| CORRIGIDO - Baseado no Script que funcionou                      |
//+------------------------------------------------------------------+
#property copyright "MacTester"
#property version   "2.00"
#property strict

//--- PARAMETROS IDENTICOS AO SCRIPT/PYTHON
input double InpMinAmplitudeMult = 1.35;
input double InpMinVolumeMult    = 1.3;
input double InpMaxSombraPct     = 0.30;
input int    InpLookbackAmplitude = 25;
input int    InpLookbackVolume    = 20;
input int    InpHoraInicio        = 9;
input int    InpMinutoInicio      = 15;
input int    InpHoraFim           = 11;
input int    InpMinutoFim         = 0;
input double InpSL_ATR_Mult      = 2.0;     // PYTHON: sl_atr_mult
input double InpTP_ATR_Mult      = 3.0;     // PYTHON: tp_atr_mult
input int    InpHoraFechamento   = 12;      // PYTHON: Fecha às 12h15
input int    InpMinutoFechamento = 15;      // PYTHON: Fecha às 12h15
input double InpLotSize          = 1.0;
input int    InpMagicNumber      = 123456;

//--- Globais
datetime barraElefante = 0;  // Timestamp da barra elefante (PYTHON LOGIC)
double maximaElefante = 0;
double minimaElefante = 0;
string direcaoElefante = "";
int totalTrades = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   Print("========================================");
   Print("EA BARRA ELEFANTE - CORRIGIDO V2");
   Print("========================================");
   Print("Parametros identicos ao Script que funcionou");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("========================================");
   Print("EA FINALIZADO - Total Trades: ", totalTrades);
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
   
   // IMPORTANTE: Verificar fechamento intraday ANTES de verificar posição
   VerificarFechamentoIntraday();
   
   // Se tem posicao, NAO detecta novos elefantes
   if(PositionSelect(_Symbol))
      return;
   
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
void VerificarFechamentoIntraday()
{
   if(!PositionSelect(_Symbol))
      return;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Fechar às 12h15 (PYTHON: INTRADAY_CLOSE)
   if(dt.hour > InpHoraFechamento || (dt.hour == InpHoraFechamento && dt.min >= InpMinutoFechamento))
   {
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_DEAL;
      request.symbol = _Symbol;
      request.volume = PositionGetDouble(POSITION_VOLUME);
      request.position = PositionGetInteger(POSITION_TICKET);
      request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      request.price = (request.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      request.deviation = 10;
      request.magic = InpMagicNumber;
      
      OrderSend(request, result);
   }
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
   MqlRates ratesAmp[];
   if(CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackAmplitude, ratesAmp) <= 0)
      return;
   
   double somaAmp = 0;
   for(int i = 0; i < InpLookbackAmplitude; i++)
      somaAmp += (ratesAmp[i].high - ratesAmp[i].low);
   
   double ampMedia = somaAmp / InpLookbackAmplitude;
   
   MqlRates ratesVol[];
   if(CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackVolume, ratesVol) <= 0)
      return;
   
   double somaVol = 0;
   for(int i = 0; i < InpLookbackVolume; i++)
      somaVol += (double)ratesVol[i].real_volume;
   
   double volMedia = somaVol / InpLookbackVolume;
   
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
      AbrirPosicao(tipo);
   }
   
   // PYTHON LOGIC: Limpar elefante (rompeu ou nao, esquece)
   barraElefante = 0;
}

//+------------------------------------------------------------------+
void AbrirPosicao(ENUM_ORDER_TYPE tipo)
{
   // Calcular ATR
   MqlRates rates[];
   if(CopyRates(_Symbol, PERIOD_M5, 0, 15, rates) <= 0)
      return;
   
   double soma = 0;
   for(int i = 1; i <= 14; i++)
   {
      double high = rates[i].high;
      double low = rates[i].low;
      double close_prev = rates[i-1].close;
      
      double tr = MathMax(high - low, 
                  MathMax(MathAbs(high - close_prev), 
                         MathAbs(low - close_prev)));
      soma += tr;
   }
   
   double atr = soma / 14;
   
   // Preco
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   
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
   request.comment = "BarraElefante_V2";
   
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         totalTrades++;
         if(totalTrades % 10 == 0)
            Print("Trade #", totalTrades, " aberto: ", EnumToString(tipo));
      }
   }
}
//+------------------------------------------------------------------+

