//+------------------------------------------------------------------+
//|                                    EA_BarraElefante_NOVO.mq5     |
//|                        EA LIMPO baseado no script que FUNCIONA   |
//|                        Logica comprovadamente correta            |
//+------------------------------------------------------------------+
#property copyright "MacTester V2.0"
#property link      ""
#property version   "2.00"
#property description "EA Barra Elefante - Logica Simplificada e Correta"

//--- Parametros
input group "===== DETECCAO ELEFANTE ====="
input double   InpMinAmplitudeMult = 1.35;
input double   InpMinVolumeMult = 1.3;
input double   InpMaxSombraPct = 0.3;
input int      InpLookbackAmplitude = 25;

input group "===== HORARIOS ====="
input int      InpHorarioInicio = 9;
input int      InpMinutoInicio = 15;
input int      InpHorarioFimEntradas = 11;
input int      InpMinutoFimEntradas = 0;
input int      InpHorarioFechamento = 12;
input int      InpMinutoFechamento = 15;
input bool     InpFecharIntraday = true;

input group "===== GESTAO RISCO ====="
input double   InpSL_ATR_Mult = 2.0;
input double   InpTP_ATR_Mult = 3.0;
input double   InpLotSize = 1.0;
input int      InpMagicNumber = 240111;
input string   InpTradeComment = "BE_NOVO";

input group "===== INDICADORES ====="
input int      InpATR_Period = 14;

//--- Variaveis globais
int handleATR;
datetime lastBarTime = 0;
datetime elefanteDetectadoTime = 0;
bool aguardandoRompimento = false;
double elefanteHigh = 0;
double elefanteLow = 0;
bool elefanteBull = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   handleATR = iATR(_Symbol, PERIOD_CURRENT, InpATR_Period);
   if(handleATR == INVALID_HANDLE)
   {
      Print("ERRO: Nao foi possivel criar ATR!");
      return INIT_FAILED;
   }
   
   Print("========================================");
   Print("EA Barra Elefante NOVO inicializado");
   Print("========================================");
   Print("Amplitude min: ", InpMinAmplitudeMult, "x");
   Print("Volume min: ", InpMinVolumeMult, "x");
   Print("Sombra max: ", InpMaxSombraPct * 100, "%");
   Print("Lookback: ", InpLookbackAmplitude);
   Print("Horario: ", InpHorarioInicio, "h", InpMinutoInicio, " a ", 
         InpHorarioFimEntradas, "h", InpMinutoFimEntradas);
   Print("Fechamento: ", InpHorarioFechamento, "h", InpMinutoFechamento);
   Print("========================================");
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(handleATR != INVALID_HANDLE)
      IndicatorRelease(handleATR);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Se aguardando rompimento, verificar a cada tick
   if(aguardandoRompimento)
   {
      CheckRompimento();
      return;
   }
   
   // Detectar elefante apenas em nova barra
   datetime currentTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentTime == lastBarTime)
      return;
   
   lastBarTime = currentTime;
   
   // Fechar posicoes no final do dia
   if(InpFecharIntraday)
      CheckFecharIntraday();
   
   // CANCELAR aguardando se passou mais de 1 barra
   if(aguardandoRompimento)
   {
      // Calcular tempo limite: elefante + 2 barras (5min * 2 = 10min)
      // Se passou desse tempo, cancelar
      datetime tempoLimite = elefanteDetectadoTime + PeriodSeconds(PERIOD_CURRENT) * 2;
      if(currentTime > tempoLimite)
      {
         Print("AGUARDANDO ROMPIMENTO CANCELADO: Passou tempo limite");
         aguardandoRompimento = false;
      }
   }
   
   // Se tem posicao aberta, nao detectar novos elefantes
   if(PositionSelect(_Symbol))
   {
      aguardandoRompimento = false;
      return;
   }
   
   // Detectar barra elefante
   DetectarElefante();
}

//+------------------------------------------------------------------+
//| Detectar Barra Elefante                                          |
//+------------------------------------------------------------------+
void DetectarElefante()
{
   // Copiar dados suficientes (incluindo historico)
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   int bars_needed = InpLookbackAmplitude + 2;
   if(CopyRates(_Symbol, PERIOD_CURRENT, 0, bars_needed, rates) < bars_needed)
      return;
   
   // Barra fechada = rates[1]
   MqlDateTime time_struct;
   TimeToStruct(rates[1].time, time_struct);
   int hora = time_struct.hour;
   int minuto = time_struct.min;
   
   // FILTRO 1: Horario
   // ANTES de 9h15: bloqueia
   if(hora < InpHorarioInicio || (hora == InpHorarioInicio && minuto < InpMinutoInicio))
      return;
   // DEPOIS de 11h00: bloqueia (11h01+)
   // 11h00 PERMITE, 11h01+ BLOQUEIA
   if(hora > InpHorarioFimEntradas || (hora == InpHorarioFimEntradas && minuto > InpMinutoFimEntradas))
      return;
   
   // FILTRO 2: Calcular amplitude media (25 barras ANTERIORES)
   double amplitudeMedia = 0;
   for(int i = 2; i <= InpLookbackAmplitude + 1; i++)
   {
      amplitudeMedia += (rates[i].high - rates[i].low);
   }
   amplitudeMedia /= InpLookbackAmplitude;
   
   // FILTRO 3: Calcular volume media (20 barras ANTERIORES)
   int volumeLookback = 20;
   double volumeMedia = 0;
   for(int i = 2; i <= volumeLookback + 1; i++)
   {
      volumeMedia += (double)rates[i].real_volume;
   }
   volumeMedia /= volumeLookback;
   
   // Dados da barra candidata
   double amplitude = rates[1].high - rates[1].low;
   double corpo = MathAbs(rates[1].close - rates[1].open);
   double volume = (double)rates[1].real_volume;
   
   // FILTRO 4: Amplitude
   if(amplitude < amplitudeMedia * InpMinAmplitudeMult)
   {
      Print("FILTRO AMP BLOQUEOU: ", amplitude, " < ", amplitudeMedia * InpMinAmplitudeMult);
      return;
   }
   
   // FILTRO 5: Volume
   if(volume < volumeMedia * InpMinVolumeMult)
   {
      Print("FILTRO VOL BLOQUEOU: ", volume, " < ", volumeMedia * InpMinVolumeMult);
      return;
   }
   
   // FILTRO 6: Corpo (sombra)
   double pctCorpo = (amplitude > 0) ? (corpo / amplitude) : 0;
   double limiteCorpo = 1 - InpMaxSombraPct;
   Print("DEBUG SOMBRA: Corpo=", corpo, " Amp=", amplitude, " pctCorpo=", pctCorpo, " Limite=", limiteCorpo);
   if(pctCorpo < limiteCorpo)
   {
      Print("FILTRO SOMBRA BLOQUEOU: ", pctCorpo * 100, "% < ", limiteCorpo * 100, "%");
      return;
   }
   
   // FILTRO 7: DOJI (corpo < 1 ponto = DOJI)
   if(corpo < 1.0)
   {
      Print("FILTRO DOJI BLOQUEOU: Corpo = ", corpo, " pts");
      return;
   }
   
   // FILTRO 8: Direcao
   bool isBull = false;
   bool isBear = false;
   
   if(rates[1].close > rates[1].open)
      isBull = true;
   else if(rates[1].close < rates[1].open)
      isBear = true;
   else
   {
      Print("FILTRO DIRECAO BLOQUEOU: Close = Open (DOJI exato)");
      return; // DOJI exato
   }
   
   // ELEFANTE DETECTADO!
   Print("======================================================================");
   Print("ELEFANTE DETECTADO!");
   Print("======================================================================");
   Print("  Time: ", TimeToString(rates[1].time, TIME_DATE|TIME_MINUTES));
   Print("  OHLC: O=", rates[1].open, " H=", rates[1].high, " L=", rates[1].low, " C=", rates[1].close);
   Print("  Direcao: ", isBull ? "BULL" : "BEAR");
   Print("  Amplitude: ", amplitude, " vs Media=", amplitudeMedia, " (", amplitude/amplitudeMedia, "x) Limite=", InpMinAmplitudeMult, "x");
   Print("  Volume: ", volume, " vs Media=", volumeMedia, " (", volume/volumeMedia, "x) Limite=", InpMinVolumeMult, "x");
   Print("  Corpo: ", corpo, " (", pctCorpo * 100, "%) Limite=", limiteCorpo * 100, "%");
   Print("======================================================================");
   
   // Guardar dados para aguardar rompimento
   elefanteDetectadoTime = rates[1].time;
   elefanteHigh = rates[1].high;
   elefanteLow = rates[1].low;
   elefanteBull = isBull;
   aguardandoRompimento = true;
}

//+------------------------------------------------------------------+
//| Verificar rompimento                                              |
//+------------------------------------------------------------------+
void CheckRompimento()
{
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   bool rompeu = false;
   bool isLong = false;
   
   Print("VERIFICANDO ROMPIMENTO: Elefante=", (elefanteBull?"BULL":"BEAR"), 
         " High=", elefanteHigh, " Low=", elefanteLow, " Ask=", ask, " Bid=", bid);
   
   if(elefanteBull && ask > elefanteHigh)
   {
      rompeu = true;
      isLong = true;
      Print("ROMPEU! BULL ask=", ask, " > high=", elefanteHigh);
   }
   else if(!elefanteBull && bid < elefanteLow)
   {
      rompeu = true;
      isLong = false;
      Print("ROMPEU! BEAR bid=", bid, " < low=", elefanteLow);
   }
   
   if(!rompeu)
      return;
   
   // CORRECAO CRITICA: Verificar horario ATUAL antes de abrir posicao!
   // Se o rompimento acontecer FORA DO HORARIO, NAO abrir!
   MqlDateTime time_struct_now;
   TimeToStruct(TimeCurrent(), time_struct_now);
   int hora_atual = time_struct_now.hour;
   int minuto_atual = time_struct_now.min;
   
   // Verificar se esta ANTES de 9h15
   if(hora_atual < InpHorarioInicio || (hora_atual == InpHorarioInicio && minuto_atual < InpMinutoInicio))
   {
      Print("ROMPIMENTO FORA DO HORARIO (antes 9h15) - CANCELADO");
      aguardandoRompimento = false;
      return;
   }
   
   // Verificar se esta DEPOIS de 11h00 (11h01+)
   if(hora_atual > InpHorarioFimEntradas || (hora_atual == InpHorarioFimEntradas && minuto_atual > InpMinutoFimEntradas))
   {
      Print("ROMPIMENTO FORA DO HORARIO (depois 11h00) - CANCELADO");
      aguardandoRompimento = false;
      return;
   }
   
   // ROMPEU! Abrir posicao
   aguardandoRompimento = false;
   
   Print("ROMPIMENTO DETECTADO!");
   Print("  Tipo: ", isLong ? "LONG" : "SHORT");
   
   // Copiar ATR
   double atrBuffer[];
   ArraySetAsSeries(atrBuffer, true);
   if(CopyBuffer(handleATR, 0, 0, 3, atrBuffer) < 3)
   {
      Print("ERRO: Nao foi possivel copiar ATR!");
      return;
   }
   
   double atr = atrBuffer[1];
   
   // Calcular SL e TP
   double entryPrice = isLong ? elefanteHigh : elefanteLow;
   double sl = isLong ? (entryPrice - InpSL_ATR_Mult * atr) : (entryPrice + InpSL_ATR_Mult * atr);
   double tp = isLong ? (entryPrice + InpTP_ATR_Mult * atr) : (entryPrice - InpTP_ATR_Mult * atr);
   
   // Normalizar precos
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   sl = MathRound(sl / tickSize) * tickSize;
   tp = MathRound(tp / tickSize) * tickSize;
   
   // Enviar ordem
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = InpLotSize;
   request.type = isLong ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price = isLong ? ask : bid;
   request.sl = sl;
   request.tp = tp;
   request.deviation = 10;
   request.magic = InpMagicNumber;
   request.comment = InpTradeComment;
   request.type_filling = GetFillingMode();
   
   if(!OrderSend(request, result))
   {
      Print("ERRO ao enviar ordem: ", GetLastError());
      Print("  Retcode: ", result.retcode);
   }
   else
   {
      Print("ORDEM ENVIADA!");
      Print("  Ticket: ", result.order);
      Print("  Entry: ", entryPrice);
      Print("  SL: ", sl);
      Print("  TP: ", tp);
   }
}

//+------------------------------------------------------------------+
//| Fechar posicoes no final do dia                                  |
//+------------------------------------------------------------------+
void CheckFecharIntraday()
{
   if(!PositionSelect(_Symbol))
      return;
   
   MqlDateTime time_struct;
   TimeToStruct(TimeCurrent(), time_struct);
   
   int hora = time_struct.hour;
   int minuto = time_struct.min;
   
   if(hora > InpHorarioFechamento || (hora == InpHorarioFechamento && minuto >= InpMinutoFechamento))
   {
      Print("Fechando posicao intraday...");
      
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_DEAL;
      request.symbol = _Symbol;
      request.volume = PositionGetDouble(POSITION_VOLUME);
      request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      request.price = (request.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      request.deviation = 10;
      request.magic = InpMagicNumber;
      request.comment = "INTRADAY_CLOSE";
      request.type_filling = GetFillingMode();
      
      OrderSend(request, result);
   }
}

//+------------------------------------------------------------------+
//| Helper: Obter filling mode                                       |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillingMode()
{
   int filling = (int)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   
   if((filling & 4) == 4)
      return ORDER_FILLING_RETURN;
   if((filling & 2) == 2)
      return ORDER_FILLING_IOC;
   
   return ORDER_FILLING_FOK;
}
//+------------------------------------------------------------------+

