import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

/**
 * AnimatedSearch (versione Mac): barra di ricerca con typing, cursore
 * e scheda risultato. Mostra solo risultati reali passati nelle props.
 */
export const SearchBar: React.FC<{
  query: string;
  startFrame: number;
  resultFrame: number;
  resultTitle: string;
  resultSub?: string;
}> = ({query, startFrame, resultFrame, resultTitle, resultSub}) => {
  const frame = useCurrentFrame();
  const typed = query.slice(
    0,
    Math.max(0, Math.floor(((frame - startFrame) / 45) * query.length)),
  );
  const resultOpacity = interpolate(frame, [resultFrame, resultFrame + 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const resultY = interpolate(frame, [resultFrame, resultFrame + 12], [24, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-start',
        alignItems: 'center',
        paddingTop: 320,
        background: 'linear-gradient(160deg,#123524,#081a10)',
      }}
    >
      <div
        style={{
          width: 760,
          background: '#FFFFFF',
          borderRadius: 60,
          padding: '26px 36px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          boxShadow: '0 24px 60px rgba(0,0,0,0.45)',
        }}
      >
        <span style={{fontSize: 34}}>🔍</span>
        <span
          style={{
            fontFamily: 'Arial, sans-serif',
            fontSize: 38,
            color: '#222',
            minHeight: 46,
          }}
        >
          {typed}
          <span
            style={{
              display: 'inline-block',
              width: 3,
              height: 34,
              background: '#222',
              marginLeft: 3,
              verticalAlign: -6,
              opacity: Math.floor(frame / 12) % 2 === 0 ? 1 : 0,
            }}
          />
        </span>
      </div>
      <div
        style={{
          marginTop: 28,
          width: 760,
          background: 'rgba(255,255,255,0.08)',
          border: '1px solid rgba(255,255,255,0.18)',
          borderRadius: 20,
          padding: '24px 28px',
          opacity: resultOpacity,
          transform: `translateY(${resultY}px)`,
        }}
      >
        <div style={{fontFamily: 'Arial, sans-serif', fontSize: 36, color: '#fff', fontWeight: 700}}>
          📍 {resultTitle}
        </div>
        {resultSub ? (
          <div style={{fontFamily: 'Arial, sans-serif', fontSize: 28, color: '#9fb3a8', marginTop: 6}}>
            {resultSub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
