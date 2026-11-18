import {Easing} from 'remotion';

export type Pose={x:number;y:number;z:number;scale:number;rotate:number;rotateX:number;rotateY:number;opacity:number;stretchX:number;stretchY:number};
export type MotionKey=Partial<Pose>&{frame:number;ease?:'linear'|'out'|'in'|'inOut'|'hold'};
export type MotionTrack=readonly MotionKey[];
export const identity:Pose={x:0,y:0,z:0,scale:1,rotate:0,rotateX:0,rotateY:0,opacity:1,stretchX:1,stretchY:1};
export const unit=(x:number)=>Math.max(0,Math.min(1,x));
export const curves={linear:(x:number)=>x,out:Easing.bezier(.14,1,.24,1),in:Easing.bezier(.7,0,.9,.3),inOut:Easing.bezier(.65,0,.35,1),hold:(_x:number)=>0};
/** Sparse keys carry values forward. Every property is evaluated from absolute frame time. */
export const sampleMotion=(track:MotionTrack,frame:number,base:Pose=identity):Pose=>{
 if(!track.length)return {...base};
 let previous={...base};
 const states=track.map(k=>{previous={...previous,...k};return {...previous}});
 if(frame<=track[0].frame)return states[0];
 for(let i=1;i<track.length;i++)if(frame<=track[i].frame){
  const a=track[i-1],b=track[i];const t=curves[b.ease||'out'](unit((frame-a.frame)/(b.frame-a.frame)));
  const out={...base};for(const k of Object.keys(base) as (keyof Pose)[])out[k]=states[i-1][k]+(states[i][k]-states[i-1][k])*t;
  return out;
 }
 return states[states.length-1];
};
export const poseTransform=(p:Pose)=>`translate3d(${p.x}px,${p.y}px,${p.z}px) rotateZ(${p.rotate}deg) rotateY(${p.rotateY}deg) rotateX(${p.rotateX}deg) scale(${p.scale*p.stretchX},${p.scale*p.stretchY})`;
export const between=(f:number,start:number,end:number)=>unit((f-start)/(end-start));
