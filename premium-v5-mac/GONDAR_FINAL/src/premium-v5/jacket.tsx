import type {CSSProperties} from 'react';
import {Img,staticFile,useCurrentFrame} from 'remotion';
import {frameOf,sourceTurnFrame,type Director,type CueRef} from './core';
export type TurntableAsset={folder:string;pattern:string;turnFrom:number;turnTo:number;fps:number;rotationDegrees:number;provenance:string};
export const BakedJacket3D=({director,asset,turnStart,turnEnd,left=0,top=560,width=1080,height=1200,style}:{director:Director;asset:TurntableAsset;turnStart:CueRef;turnEnd:CueRef;left?:number;top?:number;width?:number;height?:number;style?:CSSProperties})=>{
 const f=useCurrentFrame(),start=frameOf(director,turnStart),end=frameOf(director,turnEnd),source=sourceTurnFrame(f,start,end,asset.turnFrom,asset.turnTo);
 const file=asset.pattern.replace('{frame}',String(source)).replace(/\{frame:(\d+)\}/g,(_,digits)=>String(source).padStart(Number(digits),'0'));
 return <Img src={staticFile(`${asset.folder}/${file}`)} style={{position:'absolute',left,top,width,height,...style}}/>;
};
export function checkTurntableRetime(d:Director,asset:TurntableAsset,start:CueRef,end:CueRef){const sourceSeconds=(asset.turnTo-asset.turnFrom)/asset.fps,targetSeconds=(frameOf(d,end)-frameOf(d,start))/d.fps;return {sourceSeconds,targetSeconds,motionBlurNeedsRebake:Math.abs(sourceSeconds-targetSeconds)>1/d.fps,rotationDegrees:asset.rotationDegrees};}
