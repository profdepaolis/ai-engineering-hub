import type {CSSProperties} from 'react';
import {useCurrentFrame} from 'remotion';
import {PALETTE,frameOf,glyphRangeProgress,trackTypingCamera,type Director,type Glyph} from './core';
export const AnimatedUnderline=({progress,width,color=PALETTE.white,thickness=7,height=24}:{progress:number;width:number;color?:string;thickness?:number;height?:number})=><svg width={width+8} height={height} style={{display:'block',overflow:'visible'}}><path d={`M 0 ${height/2} Q ${width*.4} ${height/2-5} ${width} ${height/2}`} fill="none" stroke={color} strokeWidth={thickness} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-Math.max(0,Math.min(1,progress))}/></svg>;
export type UnderlineRange={first:number;last:number;color?:string;thickness?:number};
export type TypingCameraProps={director:Director;glyphs:readonly Glyph[];left?:number;top?:number;fontSize?:number;measuredFontSize:number;fontFamily?:string;color?:string;lineHeight?:number;camera?:{travelX?:number;travelY?:number;smoothingFrames?:number};underlines?:readonly UnderlineRange[];style?:CSSProperties};
/** No Reel text, cues, word timings, colors or asset namespace are imported. */
export const TypingCamera=({director,glyphs,left=130,top=825,fontSize=90,measuredFontSize,fontFamily='V3Body',color=PALETTE.white,lineHeight=1.18,camera,underlines=[],style}:TypingCameraProps)=>{
 const f=useCurrentFrame(),follow=trackTypingCamera(director,glyphs,f,camera),scale=fontSize/measuredFontSize;
 return <div style={{position:'absolute',left,top,fontSize,fontFamily,color,lineHeight:1,transform:`translate(${follow.x}px,${follow.y}px)`,textShadow:'0 3px 14px #0006',...style}}>
 {glyphs.map((g,i)=><span key={i} style={{position:'absolute',left:g.x*scale,top:g.line*fontSize*lineHeight,whiteSpace:'pre',opacity:f>=frameOf(director,g.cue)?1:0,color:g.color||color}}>{g.char}</span>)}
 {underlines.map((u,i)=>{const r=glyphRangeProgress(director,glyphs,f,u.first,u.last);return <div key={i} style={{position:'absolute',left:r.left*scale,top:r.line*fontSize*lineHeight+fontSize*1.13}}><AnimatedUnderline width={r.width*scale} progress={r.progress} color={u.color||color} thickness={u.thickness}/></div>;})}
 </div>;
};
