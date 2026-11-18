import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

/**
 * CinematicImpact (versione Mac): entrata con overshoot + maschera.
 * Il bass hit va sul frame di impatto (stesso cue nel director).
 */
export const ImpactTitle: React.FC<{
  text: string;
  startFrame: number;
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  sub?: string;
}> = ({
  text,
  startFrame,
  fontSize = 130,
  fontFamily = "'Arial Black', Arial, sans-serif",
  color = '#FFFFFF',
  sub,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({
    frame: frame - startFrame,
    fps,
    config: {damping: 11, stiffness: 220, mass: 0.8},
  });
  const opacity = interpolate(frame, [startFrame, startFrame + 3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const subOpacity = interpolate(frame, [startFrame + 18, startFrame + 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill
      style={{justifyContent: 'center', alignItems: 'center', padding: '0 80px'}}
    >
      <div
        style={{
          fontFamily,
          fontSize,
          fontWeight: 900,
          color,
          textAlign: 'center',
          lineHeight: 1.05,
          opacity,
          transform: `scale(${0.4 + 0.6 * s})`,
          textShadow: '0 10px 0 rgba(0,0,0,0.35), 0 20px 50px rgba(0,0,0,0.5)',
        }}
      >
        {text}
      </div>
      {sub ? (
        <div
          style={{
            marginTop: 18,
            fontFamily: 'Arial, sans-serif',
            fontSize: 36,
            color: '#FFD9A0',
            opacity: subOpacity,
            textAlign: 'center',
          }}
        >
          {sub}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
