import React from 'react';
import {AbsoluteFill, Img, Video, staticFile} from 'remotion';

/**
 * Sfondo scena: gradiente di default, oppure clip generata (Flow/Hailuo/Luma)
 * messa in public/clips/. Le clip AI sono solo supporto visivo.
 */
export const SceneBackground: React.FC<{
  gradient?: string;
  clip?: string;
  clipType?: 'video' | 'image';
  dim?: number;
}> = ({
  gradient = 'linear-gradient(160deg,#0b3d5c,#062a40)',
  clip,
  clipType = 'video',
  dim = 0.35,
}) => {
  return (
    <AbsoluteFill style={{background: gradient}}>
      {clip ? (
        clipType === 'video' ? (
          <Video
            src={staticFile(clip)}
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
        ) : (
          <Img
            src={staticFile(clip)}
            style={{width: '100%', height: '100%', objectFit: 'cover'}}
          />
        )
      ) : null}
      <AbsoluteFill style={{background: `rgba(0,0,0,${dim})`}} />
    </AbsoluteFill>
  );
};
