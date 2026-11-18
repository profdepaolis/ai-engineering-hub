import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

/**
 * Sottolineatura disegnata con SVG pathLength, legata ai frame reali.
 */
export const AnimatedUnderline: React.FC<{
  startFrame: number;
  endFrame: number;
  width?: number;
  color?: string;
  thickness?: number;
  top?: number;
}> = ({
  startFrame,
  endFrame,
  width = 640,
  color = '#FFD166',
  thickness = 10,
  top = 980,
}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center'}}>
      <svg
        width={width}
        height={30}
        viewBox={`0 0 ${width} 30`}
        style={{marginTop: top}}
      >
        <path
          d={`M6 20 Q ${width / 2} 6 ${width - 6} 18`}
          stroke={color}
          strokeWidth={thickness}
          fill="none"
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - progress}
        />
      </svg>
    </AbsoluteFill>
  );
};
