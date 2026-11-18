import React from 'react';
import {AbsoluteFill, Audio, Loop, OffthreadVideo, Sequence, staticFile} from 'remotion';
import {KineticCaption, SceneBackground, TypingTitle} from '../components';
import type {Caption, Director} from '../types';

export type AutomaticProps = {
  durationInFrames: number;
  title: string;
  captions: Caption[];
  audio: string;
  director: Director;
  scenes: {startFrame: number; durationInFrames: number; clip?: string; clipFrames?: number; cueId: string}[];
};

export const AutomaticReel: React.FC<AutomaticProps> = ({title, captions, audio, director, scenes}) => (
  <AbsoluteFill style={{backgroundColor: '#000'}}>
    {scenes.map((scene, i) => (
      <Sequence key={scene.cueId} from={scene.startFrame} durationInFrames={scene.durationInFrames}>
        <SceneBackground gradient={i % 2 ? 'linear-gradient(160deg,#3b2f5e,#1d1836)' : 'linear-gradient(160deg,#0b3d5c,#062a40)'} />
        {scene.clip && scene.clipFrames ? <>
          <Loop durationInFrames={scene.clipFrames}>
            <OffthreadVideo src={staticFile(scene.clip)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          </Loop>
          <AbsoluteFill style={{backgroundColor: 'rgba(0,0,0,.27)'}} />
        </> : null}
        {i === 0 ? <>
          <TypingTitle text={title} startFrame={director.keyframes[scene.cueId] - scene.startFrame} endFrame={Math.min(55, Math.max(1, scene.durationInFrames - 1))} fontSize={78} />
        </> : null}
      </Sequence>
    ))}
    <KineticCaption captions={captions} />
    <Audio src={staticFile(audio)} />
  </AbsoluteFill>
);
