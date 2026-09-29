import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { Scene1_Problem } from './scenes/Scene1_Problem';
import { Scene2_Solution } from './scenes/Scene2_Solution';
import { Scene3_Observability } from './scenes/Scene3_Observability';
import { Scene4_Results } from './scenes/Scene4_Results';
import { Subtitles } from './components/Subtitles';

export const MainVideo: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#050a14',
        fontFamily: "'Cairo', 'Outfit', sans-serif",
      }}
    >
      {/* Scene 1: Problem & False Alarms (0:00 - 0:25) -> 750 frames */}
      <Sequence from={0} durationInFrames={750} name="Scene 1: The Problem">
        <Scene1_Problem />
      </Sequence>

      {/* Scene 2: H2-PRISM Solution & 3 Pillars (0:25 - 1:00) -> 1050 frames */}
      <Sequence from={750} durationInFrames={1050} name="Scene 2: The Solution">
        <Scene2_Solution />
      </Sequence>

      {/* Scene 3: Observability & UNKNOWN (1:00 - 1:40) -> 1200 frames */}
      <Sequence from={1800} durationInFrames={1200} name="Scene 3: Observability & UNKNOWN">
        <Scene3_Observability />
      </Sequence>

      {/* Scene 4: Verification, Results & Impact (1:40 - 2:15) -> 1050 frames */}
      <Sequence from={3000} durationInFrames={1050} name="Scene 4: Results & Conclusion">
        <Scene4_Results />
      </Sequence>

      {/* Synchronized Arabic Subtitles Overlay across all scenes */}
      <Subtitles />
    </AbsoluteFill>
  );
};
