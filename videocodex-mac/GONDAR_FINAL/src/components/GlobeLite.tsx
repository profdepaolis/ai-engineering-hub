import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

/**
 * CinematicGlobe (versione Mac, leggera): sfera CSS con rotte luminose.
 * Per il globo PBR originale serve la libreria V5 sul vecchio PC.
 */
export const GlobeLite: React.FC<{
  startFrame: number;
  destinations: string[];
  size?: number;
}> = ({startFrame, destinations, size = 560}) => {
  const frame = useCurrentFrame();
  const rotate = interpolate(frame, [startFrame, startFrame + 300], [0, 40], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const dots = [
    {x: 0.32, y: 0.28},
    {x: 0.68, y: 0.42},
    {x: 0.45, y: 0.68},
    {x: 0.72, y: 0.72},
  ];
  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        background: 'radial-gradient(circle at 50% 42%, #0b3d5c 0%, #020d18 72%)',
      }}
    >
      <div
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          position: 'relative',
          background:
            'radial-gradient(circle at 35% 35%, #3fa7d6 0%, #0b3d5c 58%, #062a40 100%)',
          boxShadow:
            'inset -40px -30px 90px rgba(0,0,0,0.6), 0 0 90px rgba(63,167,214,0.35)',
          transform: `rotate(${rotate}deg)`,
        }}
      >
        {dots.slice(0, destinations.length).map((d, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: d.x * size - 14,
              top: d.y * size - 14,
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: '#FFD166',
              boxShadow: '0 0 26px #FFD166',
            }}
          />
        ))}
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{position: 'absolute', inset: 0}}
        >
          <path
            d={`M ${dots[0].x * size} ${dots[0].y * size} Q ${size / 2} ${size * 0.1} ${dots[1].x * size} ${dots[1].y * size}`}
            stroke="#FFD166"
            strokeWidth={4}
            fill="none"
            strokeDasharray="10 8"
            opacity={0.85}
          />
          <path
            d={`M ${dots[1].x * size} ${dots[1].y * size} Q ${size * 0.85} ${size * 0.55} ${dots[2].x * size} ${dots[2].y * size}`}
            stroke="#FFD166"
            strokeWidth={4}
            fill="none"
            strokeDasharray="10 8"
            opacity={0.85}
          />
        </svg>
      </div>
      <div
        style={{
          marginTop: 40,
          fontFamily: 'Arial, sans-serif',
          fontSize: 40,
          color: '#BFE3F5',
          textAlign: 'center',
        }}
      >
        {destinations.join('  →  ')}
      </div>
    </AbsoluteFill>
  );
};
