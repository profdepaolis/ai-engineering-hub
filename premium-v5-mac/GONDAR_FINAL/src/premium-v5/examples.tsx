/** Compile-checked wiring patterns, not a fixed storyboard. A new Reel supplies its own data/cues. */
import type {ReactNode} from 'react';
import {TypingCamera,PhotoMotionShutter,CinematicImpact,CinematicReveal,DirectionalHandoff,BakedJacket3D,CinematicGlobe,AnimatedSearch,SoundDesignTrack,type Director,type Glyph,type GlobeConfig,type PhotoFlight,type TurntableAsset,type UnderlineRange} from './index';
export const typographyExample=(d:Director,glyphs:Glyph[],underlines:UnderlineRange[]=[]) => <TypingCamera director={d} glyphs={glyphs} measuredFontSize={90} underlines={underlines}/>;
export const photosExample=(d:Director,photos:PhotoFlight[])=><PhotoMotionShutter director={d} photos={photos}/>;
export const titleExample=(d:Director,text:string)=><CinematicImpact director={d} text={text} size={140} width={800} track={[{at:{id:'title-settle',offset:-8},x:540,y:960,scale:1.5,opacity:0},{at:'title-settle',scale:1,opacity:1},{at:'title-exit',opacity:0}]}/>;
export const revealExample=(d:Director,content:ReactNode)=><CinematicReveal director={d} start="reveal-start" end="reveal-end" shape="circle">{content}</CinematicReveal>;
export const handoffExample=(d:Director,outgoing:ReactNode,incoming:ReactNode,id:string)=><DirectionalHandoff director={d} start="handoff-start" end="handoff-end" outgoing={outgoing} incoming={incoming} direction="left" id={id}/>;
export const garmentExample=(d:Director,asset:TurntableAsset)=><BakedJacket3D director={d} asset={asset} turnStart="garment-turn-start" turnEnd="garment-stop"/>;
export const globeExample=(d:Director,config:GlobeConfig)=><CinematicGlobe director={d} config={config}/>;
export const searchExample=(d:Director,glyphs:Glyph[])=><AnimatedSearch director={d} glyphs={glyphs} enter="search-enter" cursorStart="cursor-start" click="search-click"/>;
export const audioExample=(d:Director,mixPath:string)=><SoundDesignTrack director={d} mixPath={mixPath}/>;
