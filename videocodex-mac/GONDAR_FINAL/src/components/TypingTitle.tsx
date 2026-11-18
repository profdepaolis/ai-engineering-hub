import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import type {Director, Glyph} from '../types';
import {frameOf} from '../types';

/**
 * TypingCamera (versione Mac): rivela i caratteri in base ai cue del director.
 * I glifi arrivano da premium_tools.py plan-typing (misure reali del font).
 * Se non ci sono glifi, rivela il testo in modo uniforme tra start/end.
 */
export const TypingTitle: React.FC<{
  text: string;
  director?: Director;
  glyphs?: Glyph[];
  startFrame: number;
  endFrame: number;
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  emphasisColor?: string;
  emphasisWord?: string;
}> = ({
  text,
  director,
  glyphs,
  startFrame,
  endFrame,
  fontSize = 84,
  fontFamily = "'Arial Black', Arial, sans-serif",
  color = '#FFFFFF',
  emphasisColor = '#FFD166',
  emphasisWord,
}) => {
  const frame = useCurrentFrame();

  let visible = '';
  if (glyphs && glyphs.length > 0 && director) {
    const shown = glyphs.filter((g) => frameOf(director, g.cue) <= frame);
    visible = shown.map((g) => g.char).join('');
  } else {
    const span = Math.max(1, endFrame - startFrame);
    const t = Math.min(1, Math.max(0, (frame - startFrame) / span));
    visible = text.slice(0, Math.floor(t * text.length));
  }

  const render = (s: string) => {
    if (!emphasisWord) {
      return s;
    }
    const idx = s.toLowerCase().indexOf(emphasisWord.toLowerCase());
    if (idx < 0) {
      return s;
    }
    return (
      <>
        {s.slice(0, idx)}
        <span style={{color: emphasisColor}}>{s.slice(idx, idx + emphasisWord.length)}</span>
        {s.slice(idx + emphasisWord.length)}
      </>
    );
  };

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 100px',
      }}
    >
      <div
        style={{
          fontFamily,
          fontSize,
          fontWeight: 900,
          color,
          textAlign: 'center',
          lineHeight: 1.15,
          textShadow: '0 6px 24px rgba(0,0,0,0.55)',
          minHeight: fontSize * 1.3,
        }}
      >
        {render(visible)}
        <span
          style={{
            display: 'inline-block',
            width: 4,
            height: fontSize * 0.9,
            background: emphasisColor,
            marginLeft: 4,
            verticalAlign: -fontSize * 0.08,
            opacity: frame < endFrame ? (Math.floor(frame / 12) % 2 === 0 ? 1 : 0) : 0,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
