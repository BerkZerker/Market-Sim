import { useEffect, useRef, useState } from "react";
import { createChart, CandlestickSeries, type IChartApi, type ISeriesApi, type CandlestickData, type Time } from "lightweight-charts";
import { getHistory } from "../api/client";
import { useTheme } from "../hooks/useTheme";
import Spinner from "./Spinner";

interface PriceChartProps {
  ticker: string;
  latestPrice?: number;
}

const INTERVALS = ["1m", "5m", "15m", "1h", "1d"] as const;

const THEME_COLORS = {
  light: { textColor: "#525252", gridColor: "#e5e5e5", bgOverlay: "bg-neutral-100/50" },
  dark: { textColor: "#9ca3af", gridColor: "#374151", bgOverlay: "bg-neutral-900/50" },
};

export default function PriceChart({ ticker, latestPrice }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [interval, setInterval] = useState<string>("5m");
  const [loading, setLoading] = useState(true);
  const { theme } = useTheme();

  // Create chart on mount
  useEffect(() => {
    if (!containerRef.current) return;
    const colors = THEME_COLORS[theme];
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { color: "transparent" },
        textColor: colors.textColor,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
      timeScale: { timeVisible: true, secondsVisible: false },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Update chart theme colors
  useEffect(() => {
    if (!chartRef.current) return;
    const colors = THEME_COLORS[theme];
    chartRef.current.applyOptions({
      layout: { textColor: colors.textColor },
      grid: {
        vertLines: { color: colors.gridColor },
        horzLines: { color: colors.gridColor },
      },
    });
  }, [theme]);

  // Fetch candle data on ticker/interval change
  useEffect(() => {
    setLoading(true);
    getHistory(ticker, interval)
      .then((data) => {
        if (!seriesRef.current) return;
        const candles: CandlestickData<Time>[] = data.candles.map((c) => ({
          time: c.timestamp as Time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
        seriesRef.current.setData(candles);
        chartRef.current?.timeScale().fitContent();
      })
      .catch(() => {
        seriesRef.current?.setData([]);
      })
      .finally(() => setLoading(false));
  }, [ticker, interval]);

  // Real-time update on latest price
  useEffect(() => {
    if (!latestPrice || !seriesRef.current) return;
    const now = Math.floor(Date.now() / 1000) as Time;
    seriesRef.current.update({
      time: now,
      open: latestPrice,
      high: latestPrice,
      low: latestPrice,
      close: latestPrice,
    });
  }, [latestPrice]);

  return (
    <div className="relative">
      {/* Interval selector */}
      <div className="flex gap-1 mb-2">
        {INTERVALS.map((iv) => (
          <button
            key={iv}
            onClick={() => setInterval(iv)}
            className={`px-2 py-0.5 rounded text-xs font-medium transition ${
              interval === iv
                ? "bg-blue-600 text-white"
                : "bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
            }`}
          >
            {iv}
          </button>
        ))}
      </div>

      {/* Chart container */}
      <div ref={containerRef} className="relative">
        {loading && (
          <div className={`absolute inset-0 flex items-center justify-center ${THEME_COLORS[theme].bgOverlay} z-10`}>
            <Spinner />
          </div>
        )}
      </div>
    </div>
  );
}
