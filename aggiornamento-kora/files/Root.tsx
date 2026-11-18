import React from 'react';
import {Composition} from 'remotion';
import {DemoSalento} from './reels/DemoSalento';
import {AutomaticReel, type AutomaticProps} from './reels/AutomaticReel';
import {KoraReel, type KoraProps} from './reels/KoraReel';

const initial: AutomaticProps = {
  durationInFrames: 30, title: '', captions: [], audio: '',
  director: {schemaVersion: 1, fps: 30, sampleRate: 48000, durationInFrames: 30, keyframes: {}, events: []},
  scenes: [],
};
const koraInitial: KoraProps = {durationInFrames: 90, voiceFrames: 30, introFrames: 30, outroFrames: 30,
  logo: '', logoBackground: '#0b2830', photos: [], audio: '', captions: []};

export const RemotionRoot: React.FC = () => <>
  <Composition id="DemoSalento" component={DemoSalento} durationInFrames={900} fps={30} width={1080} height={1920} />
  <Composition id="AutomaticReel" component={AutomaticReel} durationInFrames={30} fps={30} width={1080} height={1920}
    defaultProps={initial} calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})} />
  <Composition id="KoraReel" component={KoraReel} durationInFrames={90} fps={30} width={1080} height={1920}
    defaultProps={koraInitial} calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})} />
</>;
