import React from 'react';
import {AbsoluteFill,Composition,OffthreadVideo,Sequence,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import {TypingCamera, type Director, type Glyph} from '../premium-v5/index';

type Props={source:string; director:Director; glyphs:Glyph[]; left:number};
const smooth=(x:number)=>{const p=Math.max(0,Math.min(1,x));return p*p*(3-2*p);};
const Label:React.FC<{director:Director;glyphs:Glyph[];left:number}>=({director,glyphs,left})=>{
 const f=useCurrentFrame(); const opacity=Math.min(smooth(f/8),smooth((119-f)/12));
 return <AbsoluteFill style={{opacity,pointerEvents:'none'}}>
  <TypingCamera director={director} glyphs={glyphs} left={left} top={205} fontSize={72} measuredFontSize={72} fontFamily="KoraV5Body" color="#ffe0a0" camera={{travelX:10,travelY:0,smoothingFrames:4}} underlines={[{first:0,last:glyphs.length-1,color:'#d9b77c',thickness:4}]} style={{textShadow:'0 4px 16px rgba(0,0,0,.95)'}} />
 </AbsoluteFill>;
};
const Reel:React.FC<Props>=({source,director,glyphs,left})=><AbsoluteFill style={{background:'#071a20'}}>
 <style>{`@font-face { font-family: KoraV5Body; src: url('${staticFile('arialbd.ttf')}'); font-weight: normal; }`}</style>
 <OffthreadVideo muted src={staticFile(source)} style={{width:'100%',height:'100%',objectFit:'cover'}} />
 <Sequence from={246} durationInFrames={120}><Label director={director} glyphs={glyphs} left={left}/></Sequence>
</AbsoluteFill>;
const Root:React.FC=()=> <Composition id="KoraV5Originale" component={Reel} width={1080} height={1920} fps={30} durationInFrames={1598} defaultProps={{source:'',director:{fps:30,durationInFrames:120,events:[]},glyphs:[],left:0}}/>;
registerRoot(Root);
