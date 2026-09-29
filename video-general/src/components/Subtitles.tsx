import React from 'react';
import { useCurrentFrame } from 'remotion';
import { GENERAL_SCRIPT_SUBTITLES, SceneSubtitle } from '../types';

export const Subtitles: React.FC = () => {
  const frame = useCurrentFrame();

  const currentSub = GENERAL_SCRIPT_SUBTITLES.find(
    (s: SceneSubtitle) => frame >= s.startFrame && frame <= s.endFrame
  );

  if (!currentSub) return null;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 30,
        left: 60,
        right: 60,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 100,
        direction: 'rtl',
      }}
    >
      <div
        style={{
          backgroundColor: '#0f172a',
          padding: '14px 32px',
          borderRadius: '10px',
          border: '1px solid #334155',
          textAlign: 'center',
          maxWidth: '1280px',
          width: '100%',
        }}
      >
        <p
          style={{
            fontSize: 24,
            fontWeight: 700,
            lineHeight: 1.4,
            color: '#ffffff',
            margin: 0,
          }}
        >
          {currentSub.text}
        </p>
      </div>
    </div>
  );
};
