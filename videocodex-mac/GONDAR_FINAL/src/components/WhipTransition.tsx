import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

/**
 * WhipTransition (versione Mac): raccordo con blur derivato dal moto.
 * Le due scene condividono la giunzione: l'uscente esce, l'entrante entra.
 */
export const WhipTransition: React.FC<{
  startFrame: number;
  endFrame: number;
  children: [React.ReactNode, React.ReactNode];
}> = ({startFrame, endFrame, children}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const blur = Math.sin(t * Math.PI) * 18;
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `translateX(${-t * 1080}px)`,
          filter: `blur(${blur}px)`,
          opacity: 1 - t * 0.2,
        }}
      >
        {children[0]}
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `translateX(${(1 - t) * 1080}px)`,
          filter: `blur(${blur}px)`,
          opacity: 0.2 + t * 0.8,
        }}
      >
        {children[1]}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
