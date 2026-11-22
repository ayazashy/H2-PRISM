import { useEffect, useRef } from 'react';
import { Flag, Pause, Play, RotateCcw, SkipBack, SkipForward } from 'lucide-react';

interface PlaybackBarProps {
  timeSeconds: number[];
  timeIndex: number;
  onChangeTimeIndex: (idx: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onStopPlay: () => void;
  speed: number;
  onChangeSpeed: (s: number) => void;
  onsetTime: number | null;
}

export function PlaybackBar({
  timeSeconds,
  timeIndex,
  onChangeTimeIndex,
  isPlaying,
  onTogglePlay,
  onStopPlay,
  speed,
  onChangeSpeed,
  onsetTime,
}: PlaybackBarProps) {
  const rafRef = useRef<number | null>(null);
  const lastFrameRef = useRef<number | null>(null);
  const indexRef = useRef<number>(timeIndex);
  const simTimeRef = useRef<number>(timeSeconds[timeIndex] ?? 0);

  // Sync refs when user scrubs or scenario changes
  useEffect(() => {
    indexRef.current = timeIndex;
    simTimeRef.current = timeSeconds[timeIndex] ?? 0;
  }, [timeIndex, timeSeconds]);

  // Smooth RAF loop that does NOT tear down on every timeIndex tick
  useEffect(() => {
    if (!isPlaying || timeSeconds.length < 2) {
      lastFrameRef.current = null;
      return;
    }

    const maxT = timeSeconds[timeSeconds.length - 1];
    // If starting from the very end, loop back to 0
    if (indexRef.current >= timeSeconds.length - 1) {
      indexRef.current = 0;
      simTimeRef.current = timeSeconds[0];
      onChangeTimeIndex(0);
    }

    const tick = (now: number) => {
      if (lastFrameRef.current !== null) {
        const dtSec = Math.min(0.1, (now - lastFrameRef.current) / 1000) * speed;
        simTimeRef.current += dtSec;

        if (simTimeRef.current >= maxT) {
          indexRef.current = timeSeconds.length - 1;
          onChangeTimeIndex(timeSeconds.length - 1);
          onStopPlay();
          return;
        }

        let nextIdx = indexRef.current;
        while (nextIdx + 1 < timeSeconds.length && timeSeconds[nextIdx + 1] <= simTimeRef.current) {
          nextIdx++;
        }
        if (nextIdx !== indexRef.current) {
          indexRef.current = nextIdx;
          onChangeTimeIndex(nextIdx);
        }
      }
      lastFrameRef.current = now;
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      lastFrameRef.current = null;
    };
  }, [isPlaying, speed, timeSeconds, onChangeTimeIndex, onStopPlay]);

  const jumpToOnset = () => {
    if (onsetTime === null || timeSeconds.length === 0) return;
    let best = 0;
    let bestDiff = Infinity;
    for (let i = 0; i < timeSeconds.length; i++) {
      const diff = Math.abs(timeSeconds[i] - onsetTime);
      if (diff < bestDiff) {
        bestDiff = diff;
        best = i;
      }
    }
    onChangeTimeIndex(best);
  };

  // Keyboard shortcuts: Space (play/pause), Left/Right (step), O (onset)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
      if (e.code === 'Space') {
        e.preventDefault();
        onTogglePlay();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        onChangeTimeIndex(Math.min(timeSeconds.length - 1, indexRef.current + 1));
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        onChangeTimeIndex(Math.max(0, indexRef.current - 1));
      } else if (e.key.toLowerCase() === 'o' && onsetTime !== null) {
        e.preventDefault();
        jumpToOnset();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  const currentT = timeSeconds[timeIndex] ?? 0;
  const minT = timeSeconds[0] ?? 0;
  const maxT = timeSeconds[timeSeconds.length - 1] ?? 0;
  const onsetPct =
    onsetTime !== null && maxT > minT
      ? Math.max(0, Math.min(100, ((onsetTime - minT) / (maxT - minT)) * 100))
      : null;
  const isPostOnset = onsetTime !== null && currentT >= onsetTime;

  return (
    <footer className="playback-bar" aria-label="Time replay controls">
      <div className="transport-btns">
        <button
          type="button"
          className="btn-primary"
          onClick={onTogglePlay}
          title="Play / Pause (Space)"
        >
          {isPlaying ? <Pause size={15} /> : <Play size={15} />}
          {isPlaying ? 'Pause' : 'Play'}
        </button>

        <button
          type="button"
          className="seg-btn"
          aria-label="Step backward"
          title="Step back (←)"
          onClick={() => onChangeTimeIndex(Math.max(0, timeIndex - 1))}
        >
          <SkipBack size={14} />
        </button>

        <button
          type="button"
          className="seg-btn"
          aria-label="Step forward"
          title="Step forward (→)"
          onClick={() => onChangeTimeIndex(Math.min(timeSeconds.length - 1, timeIndex + 1))}
        >
          <SkipForward size={14} />
        </button>

        <button
          type="button"
          className="seg-btn"
          aria-label="Reset to start"
          title="Reset to t = 0"
          onClick={() => {
            onStopPlay();
            onChangeTimeIndex(0);
          }}
        >
          <RotateCcw size={14} />
        </button>

        {onsetTime !== null && (
          <button
            type="button"
            className={`seg-btn ${isPostOnset ? 'onset-active' : ''}`}
            onClick={jumpToOnset}
            title="Jump to event onset (O)"
          >
            <Flag size={13} />
            Onset ({onsetTime.toFixed(1)}s)
          </button>
        )}
      </div>

      <div className="scrubber-wrap">
        <input
          type="range"
          className="scrubber"
          aria-label="Replay timestamp scrubber"
          min={0}
          max={Math.max(0, timeSeconds.length - 1)}
          value={timeIndex}
          onChange={(e) => onChangeTimeIndex(Number(e.target.value))}
        />
        {onsetPct !== null && (
          <span
            className="scrubber-onset-pin"
            style={{ left: `${onsetPct}%` }}
            title={`Event onset at t = ${onsetTime?.toFixed(1)}s`}
          />
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
        {[0.5, 1, 2, 4].map((s) => (
          <button
            key={s}
            type="button"
            className={`seg-btn ${speed === s ? 'active' : ''}`}
            onClick={() => onChangeSpeed(s)}
          >
            {s}x
          </button>
        ))}
      </div>

      <div className="time-readout">
        <span className={`phase-dot ${onsetTime === null ? 'nominal' : isPostOnset ? 'active' : 'pre'}`} />
        t = {currentT.toFixed(1)}s / {maxT.toFixed(1)}s
      </div>
    </footer>
  );
}
