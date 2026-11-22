import { useEffect, useRef, useState } from 'react';
import { Download } from 'lucide-react';
import * as echarts from 'echarts';
import type { ScenarioPayloadV1, SensorChannel } from '../data/types';

interface SignalChartsProps {
  scenario: ScenarioPayloadV1;
  timeIndex: number;
  onChangeTimeIndex: (idx: number) => void;
  selectedChannelId: string | null;
}

const SERIES_COLORS = [
  '#0E3F3C',
  '#007F86',
  '#B45309',
  '#2563EB',
  '#9333EA',
  '#059669',
  '#D97706',
  '#0284C7',
  '#DC2626',
  '#4F46E5',
];

function ChannelChart({
  title,
  channels,
  timeSeconds,
  timeIndex,
  onChangeTimeIndex,
  onsetTime,
  endTime,
  selectedChannelId,
}: {
  title: string;
  channels: SensorChannel[];
  timeSeconds: number[];
  timeIndex: number;
  onChangeTimeIndex: (idx: number) => void;
  onsetTime: number | null;
  endTime: number | null;
  selectedChannelId: string | null;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const timeRef = useRef(timeSeconds);
  const onChangeRef = useRef(onChangeTimeIndex);

  useEffect(() => {
    timeRef.current = timeSeconds;
    onChangeRef.current = onChangeTimeIndex;
  }, [timeSeconds, onChangeTimeIndex]);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = echarts.init(containerRef.current);
    chartRef.current = chart;

    const zr = chart.getZr();
    const handleClick = (params: { offsetX: number; offsetY: number }) => {
      const point = [params.offsetX, params.offsetY];
      if (!chart.containPixel('grid', point)) return;
      const dataCoord = chart.convertFromPixel({ seriesIndex: 0 }, point);
      if (!Array.isArray(dataCoord) || !Number.isFinite(dataCoord[0])) return;
      const targetT = dataCoord[0];
      const ts = timeRef.current;
      let best = 0;
      let bestDiff = Infinity;
      for (let i = 0; i < ts.length; i++) {
        const diff = Math.abs(ts[i] - targetT);
        if (diff < bestDiff) {
          bestDiff = diff;
          best = i;
        }
      }
      onChangeRef.current(best);
    };
    zr.on('click', handleClick);

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(containerRef.current);

    return () => {
      zr.off('click', handleClick);
      ro.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const currentT = timeSeconds[timeIndex];
    const markLines: Record<string, unknown>[] = [
      {
        xAxis: currentT,
        lineStyle: { color: '#10263E', width: 2, type: 'solid' },
        label: { show: false },
      },
    ];
    if (onsetTime !== null) {
      markLines.push({
        xAxis: onsetTime,
        lineStyle: { color: '#B91C1C', width: 1.5, type: 'dashed' },
        label: { formatter: 'Onset', color: '#B91C1C', fontSize: 10 },
      });
    }
    if (endTime !== null && endTime < timeSeconds[timeSeconds.length - 1]) {
      markLines.push({
        xAxis: endTime,
        lineStyle: { color: '#B45309', width: 1.4, type: 'dotted' },
        label: { formatter: 'End', color: '#B45309', fontSize: 10 },
      });
    }

    chart.setOption(
      {
        animation: false,
        backgroundColor: 'transparent',
        grid: { left: 48, right: 34, top: 36, bottom: 26 },
        tooltip: {
          trigger: 'axis',
          valueFormatter: (v: unknown) =>
            v === null || v === undefined ? 'Missing (null)' : Number(v).toFixed(3),
        },
        legend: {
          top: 2,
          type: 'scroll',
          textStyle: { fontSize: 11, color: '#3D5166' },
        },
        xAxis: {
          type: 'value',
          min: timeSeconds[0],
          max: timeSeconds[timeSeconds.length - 1],
          axisLine: { lineStyle: { color: '#CBD5E1' } },
          splitLine: { lineStyle: { color: '#E2E8F0' } },
          axisLabel: {
            formatter: '{value}s',
            fontSize: 10.5,
            color: '#5C6F82',
            hideOverlap: true,
          },
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLine: { lineStyle: { color: '#CBD5E1' } },
          splitLine: { lineStyle: { color: '#E2E8F0' } },
          axisLabel: { fontSize: 10.5, color: '#5C6F82' },
        },
        series: channels.map((ch, i) => {
          const isHighlighted = selectedChannelId === ch.id;
          const color = SERIES_COLORS[i % SERIES_COLORS.length];
          return {
            name: ch.id,
            type: 'line',
            showSymbol: false,
            connectNulls: false,
            itemStyle: { color },
            lineStyle: {
              color,
              width: isHighlighted ? 3 : selectedChannelId ? 1.1 : 1.8,
              opacity: selectedChannelId && !isHighlighted ? 0.25 : 1,
            },
            data: timeSeconds.map((t, idx) => [t, ch.values[idx]]),
            markLine: i === 0 ? { symbol: 'none', silent: true, data: markLines } : undefined,
          };
        }),
      },
      true
    );
  }, [channels, timeSeconds, timeIndex, onsetTime, endTime, selectedChannelId]);

  const exportPng = () => {
    const chart = chartRef.current;
    if (!chart) return;
    const url = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#FFFFFF' });
    const a = document.createElement('a');
    a.href = url;
    a.download = `h2-prism-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`;
    a.click();
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)' }}>
          {title}
        </span>
        <button
          type="button"
          className="seg-btn"
          style={{ minHeight: 26, padding: '2px 8px', fontSize: '11px' }}
          onClick={exportPng}
          title="Export plot as PNG"
        >
          <Download size={12} />
          PNG
        </button>
      </div>
      <div ref={containerRef} style={{ width: '100%', height: 170, cursor: 'crosshair' }} />
    </div>
  );
}

export function SignalCharts({
  scenario,
  timeIndex,
  onChangeTimeIndex,
  selectedChannelId,
}: SignalChartsProps) {
  const [viewMode, setViewMode] = useState<'charts' | 'table'>('charts');
  const pressureChannels = scenario.sensor_channels.filter(
    (c) => c.variable === 'pressure' && c.observable
  );
  const flowChannels = scenario.sensor_channels.filter(
    (c) => c.variable === 'mass_flow' && c.observable
  );
  const pressureRef = pressureChannels[0]?.pressure_reference ?? 'declared';

  return (
    <section className="panel" aria-label="Time-aligned sensor measurements">
      <div className="panel-header">
        <h2 className="panel-title">Time-Aligned Signals</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>
            Click plot to scrub
          </span>
          <button
            type="button"
            className={`seg-btn ${viewMode === 'charts' ? 'active' : ''}`}
            onClick={() => setViewMode('charts')}
          >
            Plots
          </button>
          <button
            type="button"
            className={`seg-btn ${viewMode === 'table' ? 'active' : ''}`}
            onClick={() => setViewMode('table')}
          >
            Table (t={scenario.time_seconds[timeIndex]?.toFixed(1)}s)
          </button>
        </div>
      </div>

      <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {viewMode === 'charts' ? (
          <>
            {pressureChannels.length > 0 && (
              <ChannelChart
                title={`Pressure (${pressureChannels[0].unit}, ${pressureRef})`}
                channels={pressureChannels}
                timeSeconds={scenario.time_seconds}
                timeIndex={timeIndex}
                onChangeTimeIndex={onChangeTimeIndex}
                onsetTime={scenario.event.onset_time}
                endTime={scenario.event.end_time}
                selectedChannelId={selectedChannelId}
              />
            )}
            {flowChannels.length > 0 && (
              <ChannelChart
                title={`Mass Flow (${flowChannels[0].unit})`}
                channels={flowChannels}
                timeSeconds={scenario.time_seconds}
                timeIndex={timeIndex}
                onChangeTimeIndex={onChangeTimeIndex}
                onsetTime={scenario.event.onset_time}
                endTime={scenario.event.end_time}
                selectedChannelId={selectedChannelId}
              />
            )}
          </>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Channel</th>
                  <th>Target</th>
                  <th>Variable</th>
                  <th>Value at t={scenario.time_seconds[timeIndex]?.toFixed(1)}s</th>
                </tr>
              </thead>
              <tbody>
                {scenario.sensor_channels.map((ch) => {
                  const v = ch.values[timeIndex];
                  return (
                    <tr key={ch.id}>
                      <td className="mono">{ch.id}</td>
                      <td>{ch.node_or_edge}</td>
                      <td>{ch.variable}</td>
                      <td className="mono">
                        {!ch.observable
                          ? 'Absent (padded)'
                          : v !== null && v !== undefined
                          ? `${v.toFixed(3)} ${ch.unit}`
                          : 'Missing (null)'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
