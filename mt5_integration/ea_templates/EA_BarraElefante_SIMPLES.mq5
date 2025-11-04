//+------------------------------------------------------------------+
//| EA_BarraElefante_SIMPLES.mq5                                      |
//| IDENTICO AO PYTHON - SEM SLIPPAGE                               |
//+------------------------------------------------------------------+
#property copyright "MacTester"
#property version   "2.00"
#property strict

//--- PARAMETROS
input double InpMinAmplitudeMult = 1.35;
input double InpMinVolumeMult    = 1.3;
input double InpMaxSombraPct     = 0.30;
input int    InpLookbackAmplitude = 25;
input int    InpLookbackVolume    = 20;
input int    InpHoraInicio        = 9;
input int    InpMinutoInicio      = 15;
input int    InpHoraFim           = 11;
input int    InpMinutoFim         = 0;
input double InpSL_ATR_Mult      = 2.0;
input double InpTP_ATR_Mult      = 3.0;
input int    InpHoraFechamento   = 12;
input int    InpMinutoFechamento = 15;
input double InpLotSize          = 1.0;
input int    InpMagicNumber      = 123456;

//--- Globais
int totalTrades = 0;
int elefantesDetectados = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   Print("===== EA BARRA ELEFANTE - IDENTICO PYTHON (SEM SLIPPAGE) =====");
   Print("Parametros:");
   Print("  MinAmplitudeMult: ", InpMinAmplitudeMult);
   Print("  MinVolumeMult: ", InpMinVolumeMult);
   Print("  MaxSombraPct: ", InpMaxSombraPct);
   Print("  Lookback Amplitude: ", InpLookbackAmplitude);
   Print("  Lookback Volume: ", InpLookbackVolume);
   Print("  Horario: ", InpHoraInicio, ":", InpMinutoInicio, " - ", InpHoraFim, ":", InpMinutoFim);
   Print("  SL ATR: ", InpSL_ATR_Mult, " | TP ATR: ", InpTP_ATR_Mult);
   Print("  Fechamento: ", InpHoraFechamento, ":", InpMinutoFechamento);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("===== EA FINALIZADO =====");
   Print("  Elefantes detectados: ", elefantesDetectados);
   Print("  Total de trades: ", totalTrades);
   Print("========================");
}

//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBar = 0;
   datetime currentBar = iTime(_Symbol, PERIOD_M5, 0);
   
   // Processa apenas quando fecha nova barra
   if(currentBar == lastBar)
      return;
   
   lastBar = currentBar;
   
   // Fechar intraday - PYTHON: fecha às 12:15
   if(PositionSelect(_Symbol))
   {
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      
      if(dt.hour > InpHoraFechamento || (dt.hour == InpHoraFechamento && dt.min >= InpMinutoFechamento))
      {
         FecharPosicao();
      }
      
      return; // Se tem posição, não detecta novos elefantes
   }
   
   // ========================================
   // LOGICA DO PYTHON - CORRIGIDA
   // ========================================
   
   // Python processa assim:
   // - Na barra i: verifica se i-1 era elefante
   // - Se i-1 era elefante, verifica se i rompeu
   // - Se rompeu, entra na barra i+1
   
   // No EA em tempo real (quando barra nova fecha):
   // - Shift 0 = barra que acabou de fechar (é a barra i)
   // - Shift 1 = barra anterior (é a barra i-1, candidata a elefante)
   // - Se shift 1 é elefante E shift 0 rompeu → entrar agora
   
   MqlRates barraAtual[];  // Shift 0 = última barra que fechou
   if(CopyRates(_Symbol, PERIOD_M5, 0, 1, barraAtual) <= 0)
      return;
   
   MqlRates barraElefante[];  // Shift 1 = barra anterior (candidata a elefante)
   if(CopyRates(_Symbol, PERIOD_M5, 1, 1, barraElefante) <= 0)
      return;
   
   // Verificar horário da barra ELEFANTE
   MqlDateTime dt;
   TimeToStruct(barraElefante[0].time, dt);
   
   // Filtro horário: 09:15 até 11:00
   if(dt.hour < InpHoraInicio || (dt.hour == InpHoraInicio && dt.min < InpMinutoInicio))
      return;
   
   if(dt.hour > InpHoraFim || (dt.hour == InpHoraFim && dt.min > InpMinutoFim))
      return;
   
   // Calcular médias das barras ANTERIORES ao elefante (shift 2 em diante)
   MqlRates ratesAmp[];
   if(CopyRates(_Symbol, PERIOD_M5, 2, InpLookbackAmplitude, ratesAmp) <= 0)
      return;
   
   double somaAmp = 0;
   for(int i = 0; i < InpLookbackAmplitude; i++)
      somaAmp += (ratesAmp[i].high - ratesAmp[i].low);
   
   double ampMedia = somaAmp / InpLookbackAmplitude;
   
   MqlRates ratesVol[];
   if(CopyRates(_Symbol, PERIOD_M5, 2, InpLookbackVolume, ratesVol) <= 0)
      return;
   
   double somaVol = 0;
   for(int i = 0; i < InpLookbackVolume; i++)
      somaVol += (double)ratesVol[i].real_volume;
   
   double volMedia = somaVol / InpLookbackVolume;
   
   // Validar se barra SHIFT 1 é ELEFANTE
   double amplitude = barraElefante[0].high - barraElefante[0].low;
   double corpo = MathAbs(barraElefante[0].close - barraElefante[0].open);
   
   // Filtro 1: Amplitude mínima
   if(amplitude < ampMedia * InpMinAmplitudeMult)
      return;
   
   // Filtro 2: Volume mínimo
   if(barraElefante[0].real_volume < volMedia * InpMinVolumeMult)
      return;
   
   // Filtro 3: Corpo deve ser grande (sombra pequena)
   if(amplitude == 0)
      return;
   
   double pctCorpo = corpo / amplitude;
   double limiteCorpo = 1.0 - InpMaxSombraPct;
   
   if(pctCorpo < limiteCorpo)
      return;
   
   // ELEFANTE DETECTADO na barra ANTERIOR (shift 1)!
   elefantesDetectados++;
   Print("ELEFANTE #", elefantesDetectados, " detectado em ", TimeToString(barraElefante[0].time));
   
   // Agora verificar se a barra ATUAL (shift 0) rompeu o elefante
   bool rompeu = false;
   ENUM_ORDER_TYPE tipo;
   
   if(barraElefante[0].close > barraElefante[0].open)
   {
      // Elefante ALTA (verde/branco) na shift 1
      // Verifica se barra atual (shift 0) rompeu a máxima
      if(barraAtual[0].high > barraElefante[0].high)
      {
         rompeu = true;
         tipo = ORDER_TYPE_BUY;
         Print("  → Rompimento ALTA confirmado! Barra atual max=", barraAtual[0].high, 
               " > Elefante max=", barraElefante[0].high);
      }
   }
   else
   {
      // Elefante BAIXA (vermelho/preto) na shift 1
      // Verifica se barra atual (shift 0) rompeu a mínima
      if(barraAtual[0].low < barraElefante[0].low)
      {
         rompeu = true;
         tipo = ORDER_TYPE_SELL;
         Print("  → Rompimento BAIXA confirmado! Barra atual min=", barraAtual[0].low, 
               " < Elefante min=", barraElefante[0].low);
      }
   }
   
   // Se rompeu, ENTRAR AGORA
   if(rompeu)
   {
      Print("  → ENTRANDO ", EnumToString(tipo), " agora!");
      AbrirPosicao(tipo);
   }
   else
   {
      Print("  → Sem rompimento, aguardando...");
   }
}

//+------------------------------------------------------------------+
void AbrirPosicao(ENUM_ORDER_TYPE tipo)
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;
   
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
   
   double preco = (tipo == ORDER_TYPE_BUY) ? tick.ask : tick.bid;
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
   
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   sl = NormalizeDouble(MathRound(sl/tickSize)*tickSize, _Digits);
   tp = NormalizeDouble(MathRound(tp/tickSize)*tickSize, _Digits);
   preco = NormalizeDouble(preco, _Digits);
   
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
         Print("Trade #", totalTrades, ": ", EnumToString(tipo), " @ ", preco);
      }
   }
}

//+------------------------------------------------------------------+
void FecharPosicao()
{
   if(!PositionSelect(_Symbol))
      return;
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = PositionGetDouble(POSITION_VOLUME);
   request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price = (request.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   request.deviation = 10;
   request.magic = InpMagicNumber;
   
   OrderSend(request, result);
}
//+------------------------------------------------------------------+

