import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

function TradingViewChart({ data, markers, height = 400 }) {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Criar chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2B2B43',
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
      },
    });

    // Serie de candles
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    chartRef.current = { chart, candlestickSeries };
    setIsReady(true);

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [height]);

  // Atualizar dados quando mudarem
  useEffect(() => {
    if (!isReady || !chartRef.current) return;

    const { candlestickSeries } = chartRef.current;

    if (data && data.length > 0) {
      candlestickSeries.setData(data);
    }
  }, [data, isReady]);

  // Atualizar marcadores quando mudarem
  useEffect(() => {
    if (!isReady || !chartRef.current) return;

    const { candlestickSeries } = chartRef.current;

    if (markers && markers.length > 0) {
      candlestickSeries.setMarkers(markers);
    }
  }, [markers, isReady]);

  return (
    <div
      ref={chartContainerRef}
      style={{
        position: 'relative',
        width: '100%',
        height: `${height}px`,
      }}
    />
  );
}

export default TradingViewChart;

