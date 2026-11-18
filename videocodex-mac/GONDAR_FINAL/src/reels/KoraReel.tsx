import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {KineticCaption, TypingTitle} from '../components';
import type {Caption} from '../types';

type Photo = {src: string; from: number; duration: number};
export type KoraProps = {durationInFrames: number; voiceFrames: number; introFrames: number; outroFrames: number;
  logo: string; logoBackground: string; photos: Photo[]; audio: string; captions: Caption[]};

const LogoCard: React.FC<{logo: string; background: string; duration: number}> = ({logo, background, duration}) => {
  const f = useCurrentFrame();
  const opacity = Math.min(interpolate(f, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
    interpolate(f, [duration - 12, duration - 1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  return <AbsoluteFill style={{background, justifyContent: 'center', alignItems: 'center'}}>
    {logo ? <Img src={staticFile(logo)} style={{width: '70%', maxHeight: '38%', objectFit: 'contain', opacity}} /> : null}
  </AbsoluteFill>;
};

const MovingPhoto: React.FC<{photo: Photo; index: number}> = ({photo, index}) => {
  const f = useCurrentFrame();
  const scale = interpolate(f, [0, Math.max(1, photo.duration)], index % 2 ? [1.06, 1.01] : [1.01, 1.06], {extrapolateRight: 'clamp'});
  const opacity = index === 0 ? 1 : interpolate(f, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity, overflow: 'hidden'}}>
    <Img src={staticFile(photo.src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})`}} />
    <AbsoluteFill style={{backgroundColor: 'rgba(0,0,0,0.25)'}} />
  </AbsoluteFill>;
};

export const KoraReel: React.FC<KoraProps> = ({voiceFrames, introFrames, outroFrames, logo, logoBackground, photos, audio, captions}) => <AbsoluteFill style={{background: '#071a20'}}>
  <Sequence from={0} durationInFrames={introFrames}><LogoCard logo={logo} background={logoBackground} duration={introFrames} /></Sequence>
  <Sequence from={introFrames} durationInFrames={voiceFrames}>
    {photos.map((photo, i) => <Sequence key={photo.src + i} from={photo.from} durationInFrames={photo.duration}><MovingPhoto photo={photo} index={i} /></Sequence>)}
    <Sequence from={0} durationInFrames={100}><TypingTitle text="Il mare cambia ritmo" startFrame={4} endFrame={45} fontSize={78} /></Sequence>
    <KineticCaption captions={captions} />
    {audio ? <Audio src={staticFile(audio)} /> : null}
  </Sequence>
  <Sequence from={introFrames + voiceFrames} durationInFrames={outroFrames}><LogoCard logo={logo} background={logoBackground} duration={outroFrames} /></Sequence>
</AbsoluteFill>;
