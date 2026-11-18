import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import type {Caption} from '../types';
import {FPS} from '../types';

export const KineticCaption: React.FC<{
  captions: Caption[];
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  emphasisColor?: string;
  bottom?: number;
}> = ({
  captions,
  fontSize = 52,
  fontFamily = 'Arial, sans-serif',
  color = '#FFFFFF',
  emphasisColor = '#FFD166',
  bottom = 345,
}) => {
  const frame = useCurrentFrame();
  const nowMs = (frame / FPS) * 1000;
  const active = captions.find((c) => nowMs >= c.startMs && nowMs < c.endMs);
  if (!active) {
    return null;
  }
  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: bottom,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          fontFamily,
          fontSize,
          fontWeight: 700,
          color: active.emphasis ? emphasisColor : color,
          textAlign: 'center',
          maxWidth: 850,
          lineHeight: 1.2,
          textShadow: '0 3px 12px rgba(0,0,0,0.65)',
        }}
      >
        {active.text}
      </div>
    </AbsoluteFill>
  );
};
