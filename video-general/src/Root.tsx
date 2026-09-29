import React from 'react';
import { Composition } from 'remotion';
import { MainVideo } from './MainVideo';
import './index.css';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="H2-PRISM-General-Pitch"
        component={MainVideo}
        durationInFrames={4050}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
