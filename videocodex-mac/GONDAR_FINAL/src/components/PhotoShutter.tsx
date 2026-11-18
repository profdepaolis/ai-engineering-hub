import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type PhotoItem = {
  src?: string;
  label?: string;
  gradient?: string;
  from: number;
  to: number;
  x: number;
  y: number;
  rotate: number;
  width?: number;
};

/**
 * PhotoMotionShutter (versione Mac): foto che volano dentro con overshoot,
 * ombra e rotazione. Ogni atterraggio deve avere un cue shutter nel director.
 */
export const PhotoShutter: React.FC<{photos: PhotoItem[]}> = ({photos}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill>
      {photos.map((p, i) => {
        const s = spring({
          frame: frame - p.from,
          fps,
          config: {damping: 14, stiffness: 160, mass: 0.9},
        });
        const opacity = interpolate(frame, [p.from, p.from + 4], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const w = p.width ?? 520;
        const h = w * 1.25;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: p.x,
              top: p.y,
              width: w,
              height: h,
              opacity,
              transform: `translateY(${(1 - s) * 500}px) rotate(${p.rotate * (1 - s)}deg) scale(${0.6 + 0.4 * s})`,
              borderRadius: 18,
              overflow: 'hidden',
              border: '10px solid #FFFFFF',
              boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
              background: p.gradient ?? 'linear-gradient(140deg,#3fa7d6,#0b3d5c)',
            }}
          >
            {p.src ? (
              <Img src={p.src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  fontSize: 44,
                  fontFamily: 'Arial, sans-serif',
                  fontWeight: 700,
                  textAlign: 'center',
                  padding: 20,
                }}
              >
                {p.label ?? ''}
              </div>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
