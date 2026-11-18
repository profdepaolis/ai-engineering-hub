import React from 'react';
import {AbsoluteFill,OffthreadVideo,Img,Freeze,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import type {Caption} from '@remotion/captions';
import metrics from './glyph-metrics.json';
import {sampleMotion,poseTransform,unit,curves,between,type MotionTrack} from './motion';

export const RED='#e92c32',PAPER='#f7f1e5',INK='#101217';
export const Fonts=()=> <style>{`@font-face{font-family:V3Display;src:url('${staticFile('impact.ttf')}')}@font-face{font-family:V3Body;src:url('${staticFile('arialbd.ttf')}')}*{box-sizing:border-box}`}</style>;
const glyphs=metrics as Record<string,number>;

type ImpactProps={text:string;track:MotionTrack;size?:number;width?:number;fill?:string;stagger?:number;shutterAngle?:number;samples?:number;stroke?:string;strokeWidth?:number};
/** Exact subframe sampling of the authored trajectory; additive premultiplied accumulation. */
export const ImpactTitle=({text,track,size=190,width=800,fill=PAPER,stagger=.45,shutterAngle=180,samples=5,stroke=INK,strokeWidth=1}:ImpactProps)=>{
 const f=useCurrentFrame();const first=track[0]?.frame||0;
 if(f<first||f>(track[track.length-1]?.frame||0)+1)return null;
 const advance=[...text].map(c=>(glyphs[c]||.55)*size);const natural=advance.reduce((a,b)=>a+b,0),sx=width/natural;
 const offsets=advance.map((_,i)=>advance.slice(0,i).reduce((a,b)=>a+b,0)-natural/2);
 const count=Math.max(1,Math.min(9,Math.floor(samples))),shutter=shutterAngle/360;
 return <svg width="1080" height="1920" style={{position:'absolute',inset:0,overflow:'visible',isolation:'isolate',pointerEvents:'none'}} aria-label={text}>
  <g style={{isolation:'isolate'}}>{Array.from({length:count},(_,s)=>{
   const at=f-shutter*(count===1?0:s/(count-1));
   return <g key={s} opacity={1/count} style={{mixBlendMode:'plus-lighter'}}>
    {[...text].map((c,i)=>{
     const delay=at-first<16?i*stagger:0;const p=sampleMotion(track,at-delay);
     const entry=unit((at-first-i*stagger)/9),bend=Math.sin(i/Math.max(1,text.length-1)*Math.PI)*(1-entry)*-36;
     return <g key={i} opacity={p.opacity} transform={`translate(${p.x},${p.y}) rotate(${p.rotate}) scale(${p.scale*p.stretchX*sx},${p.scale*p.stretchY})`}>
      <g style={{transformBox:'fill-box',transformOrigin:'50% 50%',transform:`perspective(1000px) rotateX(${p.rotateX}deg) rotateY(${p.rotateY}deg)`}}>
       <text x={offsets[i]} y={bend} dominantBaseline="central" fontFamily="V3Display" fontSize={size} fill={fill} stroke={stroke} strokeWidth={strokeWidth} paintOrder="stroke fill">{c===' '?'\u00a0':c}</text>
      </g>
     </g>;
    })}
   </g>;
  })}</g>
 </svg>;
};

type RevealProps={children:React.ReactNode;start:number;duration:number;shape?:'circle'|'diagonal'|'horizontal';center?:[number,number];reverse?:boolean};
/** Progressive alpha aperture. The outgoing shot is retained behind this component. */
export const MaskedReveal=({children,start,duration,shape='circle',center=[540,960],reverse=false}:RevealProps)=>{
 const f=useCurrentFrame();let p=curves.inOut(between(f,start,start+duration));if(reverse)p=1-p;
 const clip=shape==='circle'?`circle(${p*2250}px at ${center[0]}px ${center[1]}px)`:shape==='diagonal'?`polygon(0 0,${p*135}% 0,${Math.max(0,p*135-35)}% 100%,0 100%)`:`inset(${(1-p)*50}% 0)`;
 return <AbsoluteFill style={{clipPath:clip,willChange:'clip-path'}}>{children}</AbsoluteFill>;
};

type CaptionProps={captions:Caption[];maxWords?:number;maxChars?:number;top?:number;size?:number;layouts?:{startMs:number;endMs:number;top:number;align?:'left'|'center';angle?:number}[]};
/** Actual timestamps drive page boundaries, active-word emphasis and phrase reflow. */
export const KineticCaption=({captions,maxWords=4,maxChars=30,top=1480,size=49,layouts=[]}:CaptionProps)=>{
 const f=useCurrentFrame(),{fps}=useVideoConfig(),ms=f/fps*1000;
 const pages:Caption[][]=[];let page:Caption[]=[];
 captions.forEach((w,i)=>{
  if(page.length&&(page.length>=maxWords||page.map(x=>x.text).join(' ').length+w.text.length>maxChars||w.startMs-page[page.length-1].endMs>250)){pages.push(page);page=[];}
  page.push(w);if(/[,.!?]$/.test(w.text)||i===captions.length-1){pages.push(page);page=[];}
 });
 const active=pages.find(p=>ms>=p[0].startMs&&ms<p[p.length-1].endMs+60);if(!active)return null;
 const layout=layouts.find(l=>ms>=l.startMs&&ms<l.endMs),y=layout?.top??top;
 const p=curves.out(unit((ms-active[0].startMs)/120));
 return <div style={{position:'absolute',left:100,right:130,top:y,padding:'7px 12px',display:'flex',justifyContent:layout?.align==='left'?'flex-start':'center',flexWrap:'wrap',gap:'7px 14px',fontFamily:'V3Body',fontSize:size,lineHeight:1.25,color:PAPER,transform:`translateY(${(1-p)*24}px) rotate(${layout?.angle||0}deg)`,textShadow:'0 2px 3px #000,0 5px 13px #000',background:'radial-gradient(ellipse,#0004,transparent 73%)'}}>
  {active.map((w,i)=>{const isActive=ms>=w.startMs&&ms<w.endMs,e=curves.out(unit((ms-w.startMs)/95));return <span key={i} style={{display:'inline-block',whiteSpace:'nowrap',position:'relative',color:isActive?PAPER:'#e7e2d9',opacity:ms<w.startMs?.50:1,transform:`translateY(${isActive?-5*(1-e):0}px) scale(${isActive?1.025:1})`}}>{w.text}<span style={{position:'absolute',left:-3,right:-3,bottom:-2,height:5,background:RED,transformOrigin:'left center',transform:`scaleX(${isActive?e:0})`}}/></span>})}
 </div>;
};

type Occlusion={videoSrc:string;maskFolder:string;sourceFrameOffset?:number;maskFrames:number};
type DepthProps={text:string;track:MotionTrack;size?:number;fill?:string;depth?:number;occlusion?:Occlusion};
/** CSS perspective planes: foreground is z=0, text travels behind/in front via actual translateZ. */
export const DepthText=({text,track,size=210,fill=PAPER,depth=9,occlusion}:DepthProps)=>{
 const f=useCurrentFrame(),p=sampleMotion(track,f),sourceFrame=Math.max(0,Math.floor(f+(occlusion?.sourceFrameOffset||0)));
 const index=Math.min((occlusion?.maskFrames||1)-1,sourceFrame);
 const mask=occlusion?staticFile(`${occlusion.maskFolder}/${String(index).padStart(3,'0')}.png`):'';
 return <AbsoluteFill style={{perspective:1200,transformStyle:'preserve-3d',pointerEvents:'none'}}>
  <div style={{position:'absolute',left:0,top:0,width:0,height:0,transformOrigin:'0 0',transformStyle:'preserve-3d',transform:poseTransform(p),opacity:p.opacity}}>
   <svg width="1080" height="1920" viewBox="-540 -960 1080 1920" style={{position:'absolute',left:-540,top:-960,overflow:'visible'}}>
    {Array.from({length:depth},(_,i)=><text key={i} x={(depth-i)*.65} y={(depth-i)*.85} dominantBaseline="central" textAnchor="middle" fontFamily="V3Display" fontSize={size} fill={i<depth-2?INK:RED}>{text}</text>)}
    <text x="0" y="0" dominantBaseline="central" textAnchor="middle" fontFamily="V3Display" fontSize={size} fill={fill} stroke={INK} strokeWidth="1" paintOrder="stroke fill">{text}</text>
   </svg>
  </div>
  {occlusion&&<AbsoluteFill style={{transform:'translateZ(0px)',maskImage:`url('${mask}')`,WebkitMaskImage:`url('${mask}')`,maskSize:'100% 100%',WebkitMaskSize:'100% 100%'}}><Freeze frame={sourceFrame}><OffthreadVideo src={staticFile(occlusion.videoSrc)} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/></Freeze></AbsoluteFill>}
 </AbsoluteFill>;
};

type CollageLayer={id:string;src:string;kind?:'image'|'video';width:number;height:number;track:MotionTrack;from?:number;sourceFrame?:number;border?:number};
type CollageProps={layers:CollageLayer[];textureSrc?:string;textureOpacity?:number;camera?:MotionTrack};
/** Independent image/video planes, local shadows, procedural texture and a shared board camera. */
export const EditorialCollage=({layers,textureSrc,textureOpacity=.12,camera=[]}:CollageProps)=>{
 const f=useCurrentFrame(),board=sampleMotion(camera,f);
 return <AbsoluteFill style={{transformStyle:'preserve-3d',perspective:1500,transform:poseTransform(board)}}>
  {layers.map(l=>{const p=sampleMotion(l.track,f);if(f<(l.from||0))return null;return <div key={l.id} style={{position:'absolute',left:-l.width/2,top:-l.height/2,width:l.width,height:l.height,transform:poseTransform(p),opacity:p.opacity,background:PAPER,padding:l.border??8,boxShadow:'0 18px 36px #0008',transformStyle:'preserve-3d'}}>
   <div style={{width:'100%',height:'100%',position:'relative',overflow:'hidden'}}>{l.kind==='video'?<Freeze frame={Math.max(0,f-(l.from||0)+(l.sourceFrame||0))}><OffthreadVideo muted src={staticFile(l.src)} style={{width:'100%',height:'100%',objectFit:'cover'}}/></Freeze>:<Img src={staticFile(l.src)} style={{width:'100%',height:'100%',objectFit:'cover'}}/>}</div>
   {textureSrc&&<Img src={staticFile(textureSrc)} style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:textureOpacity,mixBlendMode:'multiply',pointerEvents:'none'}}/>}
  </div>})}
 </AbsoluteFill>;
};

type NumberKey={frame:number;value:number;ease?:'linear'|'out'|'inOut'};
type NumberProps={keys:NumberKey[];track?:MotionTrack;size?:number;digits?:number;format?:'integer'|'hours';mode?:'reel'|'count';suffix?:string;color?:string;accent?:string;digitStagger?:number};
const numberAt=(keys:NumberKey[],f:number)=>{
 if(f<=keys[0].frame)return keys[0].value;
 for(let i=1;i<keys.length;i++)if(f<=keys[i].frame){const a=keys[i-1],b=keys[i],p=curves[b.ease||'out'](between(f,a.frame,b.frame));return a.value+(b.value-a.value)*p;}
 return keys[keys.length-1].value;
};
/** Carry-aware digit reels; optional integer counter and hours suffix. */
export const NumberCounter=({keys,track=[],size=260,digits=2,format='integer',mode='reel',suffix='',color=PAPER,accent=RED,digitStagger=0}:NumberProps)=>{
 const f=useCurrentFrame(),p=sampleMotion(track,f),value=numberAt(keys,f),h=size*1.14,w=size*.60;
 return <div style={{position:'absolute',left:0,top:0,width:0,height:0,transformOrigin:'0 0',transform:poseTransform(p),opacity:p.opacity,fontFamily:'V3Display',fontSize:size,lineHeight:1.14,color,textShadow:'2px 3px #101217,0 10px 30px #0006'}}>
  <div style={{display:'flex',width:'max-content',transform:'translate(-50%,-50%)',alignItems:'center'}}>
  {mode==='count'?<div>{Math.round(value).toString().padStart(digits,'0')}</div>:Array.from({length:digits},(_,i)=>{
   const v=numberAt(keys,f-i*digitStagger),step=10**(digits-i-1),floor=Math.floor(v/step),sub=v%step;
   const carry=step===1?v-Math.floor(v):unit(sub-(step-1));
   const digit=floor%10,next=(digit+1)%10;
   return <div key={i} style={{width:w,height:h,overflow:'hidden',position:'relative'}}><div style={{position:'absolute',left:0,top:-carry*h,width:w,textAlign:'center'}}><div style={{height:h,color}}>{digit}</div><div style={{height:h,color:accent}}>{next}</div></div></div>;
  })}
  {format==='hours'&&<div style={{letterSpacing:-4}}>:00</div>}{suffix&&<div style={{fontSize:size*.72,marginLeft:8,color:accent}}>{suffix}</div>}
  </div>
 </div>;
};

type WhipProps={outgoing:React.ReactNode;incoming:React.ReactNode;duration:number;direction?:'left'|'right'|'up'|'down';id:string};
/** Both pictures move across the same seam. Blur sigma derives from actual screen velocity. */
export const WhipTransition=({outgoing,incoming,duration,direction='left',id}:WhipProps)=>{
 const f=useCurrentFrame(),horizontal=direction==='left'||direction==='right',sign=direction==='left'||direction==='up'?-1:1;
 const travel=horizontal?1080:1920;
 const q=(at:number)=>curves.inOut(unit(at/duration));const p=q(f),velocity=Math.abs(q(f+.25)-q(f-.25))*2*travel;
 const sigma=Math.min(45,velocity*.15),filterId=`whip-${id}`;
 const layer=(node:React.ReactNode,shift:number)=><AbsoluteFill style={{transform:`translate${horizontal?'X':'Y'}(${shift}px) scale(1.085)`,filter:`url(#${filterId})`}}>{node}</AbsoluteFill>;
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <svg width="0" height="0" style={{position:'absolute'}}><defs><filter id={filterId} x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation={horizontal?`${sigma} .15`:`.15 ${sigma}`} edgeMode="duplicate"/></filter></defs></svg>
  {layer(outgoing,sign*p*travel)}{layer(incoming,-sign*(1-p)*travel)}
 </AbsoluteFill>;
};
