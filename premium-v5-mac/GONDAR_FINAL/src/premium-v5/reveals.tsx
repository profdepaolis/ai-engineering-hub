import type {ReactNode,ComponentProps} from 'react';
import {ImpactTitle,MaskedReveal,WhipTransition} from '../v3/index';
import {Sequence} from 'remotion';
import {bindMotion,frameOf,type CueMotionKey,type CueRef,type Director} from './core';
export const CinematicReveal=({director,start,end,children,...props}:{director:Director;start:CueRef;end:CueRef;children:ReactNode}&Omit<ComponentProps<typeof MaskedReveal>,'start'|'duration'|'children'>)=>{
 const from=frameOf(director,start),duration=frameOf(director,end)-from;if(duration<=0)throw Error('Reveal duration must be positive');return <MaskedReveal {...props} start={from} duration={duration}>{children}</MaskedReveal>;
};
export const CinematicImpact=({director,track,...props}:{director:Director;track:readonly CueMotionKey[]}&Omit<ComponentProps<typeof ImpactTitle>,'track'>)=><ImpactTitle {...props} track={bindMotion(director,track)}/>;
export const DirectionalHandoff=({director,start,end,...props}:{director:Director;start:CueRef;end:CueRef}&Omit<ComponentProps<typeof WhipTransition>,'duration'>)=>{const from=frameOf(director,start),duration=frameOf(director,end)-from;if(duration<=0)throw Error('Handoff duration must be positive');return <Sequence from={from} durationInFrames={duration+1} premountFor={director.fps}><WhipTransition {...props} duration={duration}/></Sequence>;};
