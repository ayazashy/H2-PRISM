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
  '#34B5A5',
  '#E5AB65',
  '#60A5FA',
  '#F472B6',
  '#91D7C6',
  '#A78BFA',
  '#FBBF24',
  '#38BDF8',
  '#FB7185',
  '#4ADE80',
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
        lineStyle: { color: '#EDF5F1', width: 2, type: 'solid' },
        label: { show: false },
      },
    ];
    if (onsetTime !== null) {
      markLines.push({
        xAxis: onsetTime,
        lineStyle: { color: '#DC776C', width: 1.5, type: 'dashed' },
        label: { formatter: 'Onset', color: '#DC776C', fontSize: 10 },
      });
    }
    if (endTime !== null && endTime < timeSeconds[timeSeconds.length - 1]) {
      markLines.push({
        xAxis: endTime,
        lineStyle: { color: '#E5AB65', width: 1.4, type: 'dotted' },
        label: { formatter: 'End', color: '#E5AB65', fontSize: 10 },
      });
    }

    chart.setOption(
      {
        animation: false,
        backgroundColor: 'transparent',
        grid: { left: 52, right: 34, top: 38, bottom: 28 },
        tooltip: {
          trigger: 'axis',
          backgroundColor: '#0B2B28',
          borderColor: '#24524A',
          textStyle: { color: '#EDF5F1', fontSize: 12, fontFamily: 'IBM Plex Mono, monospace' },
          valueFormatter: (v: unknown) =>
            v === null || v === undefined ? 'Missing (null)' : Number(v).toFixed(3),
        },
        legend: {
          top: 2,
          type: 'scroll',
          pageIconColor: '#91D7C6',
          pageIconInactiveColor: '#24524A',
          pageTextStyle: { color: '#9CB9B1', fontSize: 11 },
          textStyle: { fontSize: 11, color: '#9CB9B1' },
        },
        xAxis: {
          type: 'value',
          min: timeSeconds[0],
          max: timeSeconds[timeSeconds.length - 1],
          axisLine: { lineStyle: { color: '#24524A' } },
          splitLine: { lineStyle: { color: 'rgba(36, 82, 74, 0.45)' } },
          axisLabel: {
            formatter: '{value}s',
            fontSize: 10.5,
            color: '#9CB9B1',
            hideOverlap: true,
          },
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLine: { lineStyle: { color: '#24524A' } },
          splitLine: { lineStyle: { color: 'rgba(36, 82, 74, 0.45)' } },
          axisLabel: { fontSize: 10.5, color: '#9CB9B1' },
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
    const url = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#071F1D' });
    const a = document.createElement('a');
    a.href = url;
    a.download = `h2-prism-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`;
    a.click();
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-secondary)' }}>
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
      <div ref={containerRef} style={{ width: '100%', height: 175, cursor: 'crosshair' }} />
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

      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
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
