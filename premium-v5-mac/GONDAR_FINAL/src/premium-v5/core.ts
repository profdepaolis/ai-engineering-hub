import type {MotionKey,MotionTrack} from '../v3/motion';
export type CueRef=string|{id:string;offset?:number};
export type AudioPlacement={path:string;startSample:number;peakSample:number;targetSample:number;sampleCount:number;peakDbFS:number;fadeInMs:number;fadeOutMs:number;sha256?:string;licenseStatus?:string};
export type Director={fps:number;durationInFrames:number;sampleRate?:number;events:readonly {id:string;frame:number;phase?:string;component?:string;audio?:AudioPlacement;pan?:number}[]};
export type CueMotionKey=Omit<MotionKey,'frame'>&{at:CueRef};
export type Glyph={char:string;cue:CueRef;word:number;line:number;x:number;width:number;color?:string};
export function adaptMeasuredGlyphs(glyphs:readonly {char:string;id:string;word:number;line:number;x:number;width:number;color?:string}[]):Glyph[]{return glyphs.map(g=>({char:g.char,cue:g.id,word:g.word,line:g.line,x:g.x,width:g.width,...(g.color?{color:g.color}:{})}));}
export type ProductionMode='AUTOMATICA'|'GUIDATA'|'REGIA COMPLETA';
export function productionMode(value:string='AUTOMATICA'):ProductionMode{const mode=value.trim().toUpperCase().replace(/[_-]+/g,' ');if(mode==='AUTOMATICA'||mode==='GUIDATA'||mode==='REGIA COMPLETA')return mode;throw Error(`Unknown production mode: ${value}`);}
export const PALETTE={white:'#FFF8EF',red:'#D52B35',yellow:'#FFD166',black:'#171717'};
export const clamp=(v:number)=>Math.max(0,Math.min(1,v));
export const smooth=(v:number)=>{v=clamp(v);return v*v*(3-2*v);};
export function cue(d:Director,id:string){const e=d.events.find(e=>e.id===id);if(!e)throw Error(`Missing cue: ${id}`);return e;}
export function frameOf(d:Director,ref:CueRef){return typeof ref==='string'?cue(d,ref).frame:cue(d,ref.id).frame+(ref.offset||0);}
export function bindMotion(d:Director,keys:readonly CueMotionKey[]):MotionTrack{
 const result=keys.map(({at,...pose})=>({...pose,frame:frameOf(d,at)}));
 if(result.some((k,i)=>i>0&&k.frame<=result[i-1].frame))throw Error('Motion keys must have strictly increasing resolved frames');return result;
}
export function visibleGlyphs(d:Director,glyphs:readonly Glyph[],frame:number){return glyphs.filter(g=>frame>=frameOf(d,g.cue));}
export function trackTypingCamera(d:Director,glyphs:readonly Glyph[],frame:number,{travelX=36,travelY=10,smoothingFrames=5}:{travelX?:number;travelY?:number;smoothingFrames?:number}={}){
 let x=0,y=0;const count=Math.max(1,Math.round(smoothingFrames));
 for(let i=0;i<count;i++){const list=visibleGlyphs(d,glyphs,frame-i),g=list[list.length-1];if(!g)continue;const width=Math.max(...glyphs.filter(v=>v.line===g.line).map(v=>v.x+v.width));x+=((g.x+g.width)/Math.max(1,width)-.5)*-travelX/count;y+=-g.line*travelY/count;}return {x,y};
}
export function glyphRangeProgress(d:Director,glyphs:readonly Glyph[],frame:number,first:number,last:number,smoothingFrames=4){
 if(first<0||last<first||last>=glyphs.length)throw Error('Invalid underline glyph range');
 const range=glyphs.slice(first,last+1);if(range.some(g=>g.line!==range[0].line))throw Error('One underline cannot cross lines; split the range');
 const left=range[0].x,right=Math.max(...range.map(g=>g.x+g.width)),width=right-left;let progress=0;const count=Math.max(1,Math.round(smoothingFrames));
 for(let i=0;i<count;i++){const visible=visibleGlyphs(d,range,frame-i);progress+=(visible.length?clamp((Math.max(...visible.map(g=>g.x+g.width))-left)/Math.max(1,width)):0)/count;}return {left,width,line:range[0].line,progress};
}
export function sourceTurnFrame(frame:number,start:number,end:number,sourceStart:number,sourceEnd:number){
 if(end<=start||sourceEnd<=sourceStart)throw Error('Turntable ranges must increase');return Math.round(sourceStart+clamp((frame-start)/(end-start))*(sourceEnd-sourceStart));
}
export function routeProgress(frame:number,peak:number,arrival:number){
 if(peak>=arrival)throw Error('A route velocity peak must precede arrival');return smooth((frame-(2*peak-arrival))/(2*(arrival-peak)));
}
export function latLonXYZ(lat:number,lon:number,radius=2):[number,number,number]{
 if(!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180||radius<=0)throw Error('Invalid geographical coordinate/radius');
 const a=lat*Math.PI/180,b=lon*Math.PI/180;return [radius*Math.cos(a)*Math.cos(b),radius*Math.sin(a),-radius*Math.cos(a)*Math.sin(b)];
}
export function auditDirector(d:Director){
 const errors:string[]=[],ids=new Set<string>(),sr=d.sampleRate||48000;
 if(d.fps<=0||d.durationInFrames<=0)errors.push('Invalid fps/duration');
 for(const e of d.events){if(ids.has(e.id))errors.push(`Duplicate cue ${e.id}`);ids.add(e.id);if(!Number.isInteger(e.frame)||e.frame<0||e.frame>=d.durationInFrames)errors.push(`Out of range ${e.id}`);if(e.audio){const a=e.audio,target=Math.round(e.frame*sr/d.fps);if(a.targetSample!==target||a.startSample+a.peakSample!==target)errors.push(`Sample/frame mismatch ${e.id}`);if(a.startSample<0||a.startSample+a.sampleCount>Math.round(d.durationInFrames*sr/d.fps))errors.push(`Audio out of range ${e.id}`);}}
 return {passed:errors.length===0,errors,cueCount:d.events.length,audioCueCount:d.events.filter(e=>e.audio).length};
}
