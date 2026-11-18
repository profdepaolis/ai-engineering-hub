import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {EditorialCollage,sampleMotion,type MotionKey,type MotionTrack} from '../v3/index';
import {frameOf,type CueRef,type Director} from './core';
type PhotoPose=Omit<MotionKey,'frame'|'ease'>;
export type PhotoFlight={id:string;src:string;width:number;height:number;fly:CueRef;land:CueRef;from:PhotoPose;settle:PhotoPose;overshoot?:PhotoPose;leadInFrames?:number;overshootLeadFrames?:number;border?:number};
export function photoTrack(d:Director,p:PhotoFlight):MotionTrack{
 const start=frameOf(d,p.fly)-(p.leadInFrames??5),land=frameOf(d,p.land),over=p.overshootLeadFrames??4;
 if(land-over<=start)throw Error(`Insufficient flight time for ${p.id}`);
 return [{frame:start,opacity:1,...p.from},{frame:land-over,...(p.overshoot||{...p.settle,y:(p.settle.y||0)-25,z:35,scale:1.035}),ease:'out'},{frame:land,...p.settle,ease:'inOut'}];
}
/** fly/land events must carry distinct appropriate whoosh/shutter audio in the shared director. */
export const PhotoMotionShutter=({director,photos,blurPerPixel=.11,maxBlur=12}:{director:Director;photos:readonly PhotoFlight[];blurPerPixel?:number;maxBlur?:number})=>{
 const f=useCurrentFrame();return <AbsoluteFill>{photos.map(photo=>{const track=photoTrack(director,photo),p=sampleMotion(track,f),q=sampleMotion(track,f-.5),speed=Math.hypot(p.x-q.x,p.y-q.y);return <AbsoluteFill key={photo.id} style={{filter:`blur(${Math.min(maxBlur,speed*blurPerPixel)}px)`}}><EditorialCollage layers={[{id:photo.id,src:photo.src,width:photo.width,height:photo.height,track,from:track[0].frame,border:photo.border??11}]}/></AbsoluteFill>;})}</AbsoluteFill>;
};
