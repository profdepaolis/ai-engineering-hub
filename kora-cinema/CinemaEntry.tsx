import React from 'react';
import {AbsoluteFill, Composition, Img, OffthreadVideo, Sequence, interpolate, registerRoot, staticFile, useCurrentFrame} from 'remotion';

type Photo = {src:string; from:number; duration:number};
type Caption = {text:string; startMs:number; endMs:number; emphasis?:boolean};
type Props = {durationInFrames:number; voiceFrames:number; introFrames:number; outroFrames:number; logo:string; logoBackground:string; photos:Photo[]; captions:Caption[]; mare:string; musa:string};
const clamp = {extrapolateLeft:'clamp' as const, extrapolateRight:'clamp' as const};
const smooth = (x:number) => {const p=Math.max(0, Math.min(1,x)); return p*p*(3-2*p);};
const gold = '#d9b77c';

const Logo:React.FC<{src:string; bg:string; duration:number; ending:boolean}> = ({src,bg,duration,ending}) => {
 const f=useCurrentFrame(); const a=Math.min(smooth(f/12),smooth((duration-1-f)/12));
 const scale=1.04 - 0.04*smooth(f/30);
 return <AbsoluteFill style={{background:bg,alignItems:'center',justifyContent:'center',overflow:'hidden'}}>
  <div style={{position:'absolute',top:'20%',height:1,width:`${60*smooth(f/24)}%`,background:gold,opacity:a*.7}} />
  <Img src={staticFile(src)} style={{width:'70%',maxHeight:'38%',objectFit:'contain',opacity:a,transform:`scale(${scale})`}}/>
  <div style={{position:'absolute',bottom:'21%',height:1,width:`${60*smooth(f/24)}%`,background:gold,opacity:a*.7}} />
  {ending && <div style={{position:'absolute',bottom:'27%',color:gold,fontFamily:'Arial, sans-serif',fontWeight:600,letterSpacing:5,fontSize:24,opacity:a}}>IL MARE, DA VIVERE</div>}
 </AbsoluteFill>;
};

const MovingPhoto:React.FC<{photo:Photo; index:number}> = ({photo,index}) => {
 const f=useCurrentFrame(); const p=smooth(f / Math.max(1,photo.duration)); const enter=index===0?1:smooth(f/12);
 const direction=index%2===0 ? 1 : -1;
 const zoom=index%2===0 ? 1.09+0.10*p : 1.19-0.10*p;
 const x=direction*(-2.8+5.6*p); const y=(index%3-1)*1.7*(2*p-1);
 // Dissolve plus a restrained directional reveal, centred on the existing audio cue.
 const clip=index===0?'inset(0 0 0 0)':direction>0?`inset(0 ${(1-enter)*12}% 0 0)`:`inset(0 0 0 ${(1-enter)*12}%)`;
 return <AbsoluteFill style={{opacity:enter,clipPath:clip,overflow:'hidden'}}>
   <Img src={staticFile(photo.src)} style={{width:'100%',height:'100%',objectFit:'cover',transform:`scale(${zoom}) translate(${x}%, ${y}%)`}} />
   <AbsoluteFill style={{background:'linear-gradient(180deg, rgba(4,24,30,.34), rgba(4,24,30,.05) 40%, rgba(4,24,30,.62) 100%)'}} />
 </AbsoluteFill>;
};

const words = new Set(['mare','ritmo','silenziose','luce','morbida','bellezza','kora','bene','giorni','dicembre','colazione','aperitivo','esperienze','autentico','vivere','chiamateci','whatsapp','sempre']);
const Captions:React.FC<{captions:Caption[]}> = ({captions}) => {
 const f=useCurrentFrame(), ms=f*1000/30;
 const c=captions.find(x=>ms>=x.startMs && ms<x.endMs);
 if(!c)return null;
 const normalized=c.text.toLocaleLowerCase('it').replace(/[^a-zàèéìòù]/g,'');
 const kora=normalized==='kora'; const keyword=words.has(normalized);
 const age=Math.max(0,(ms-c.startMs)/1000*30);
 const pop=smooth(age/(kora?3:5)); const scale=kora?0.68+0.32*pop:keyword?0.84+0.16*pop:0.94+0.06*pop;
 return <AbsoluteFill style={{alignItems:'center',justifyContent:'flex-end',paddingBottom:340,pointerEvents:'none'}}>
  <div style={{fontFamily:'Arial, sans-serif',fontSize:kora?110:keyword?72:54,fontWeight:kora?900:800,color:keyword?'#ffe0a0':'#fff',textAlign:'center',maxWidth:850,lineHeight:1.18,textShadow:'0 4px 16px rgba(0,0,0,.9)',transform:`translateY(${(1-pop)*10}px) scale(${scale})`}}>{c.text}
    {keyword && <div style={{height:5,background:gold,marginTop:8,width:`${100*smooth(age/8)}%`,borderRadius:4}} />}
  </div>
 </AbsoluteFill>;
};
const Title:React.FC = () => {
 const f=useCurrentFrame(); const text='Il mare cambia ritmo';
 const shown=text.slice(0,Math.floor(text.length*smooth((f-4)/41)));
 const fade=f<78?1:1-smooth((f-78)/22);
 return <AbsoluteFill style={{justifyContent:'center',alignItems:'center',padding:'0 100px',opacity:fade}}>
  <div style={{color:'white',fontFamily:'Arial Black, Arial, sans-serif',fontWeight:900,fontSize:78,textAlign:'center',lineHeight:1.15,textShadow:'0 6px 24px rgba(0,0,0,.7)'}}>{shown}</div>
  <div style={{height:4,width:`${44*smooth((f-25)/25)}%`,background:gold,marginTop:22}} />
 </AbsoluteFill>;
};
const VideoInsert:React.FC<{src:string; duration:number}> = ({src,duration}) => {
 const f=useCurrentFrame(), fade=Math.min(smooth(f/10),smooth((duration-1-f)/10));
 return <AbsoluteFill style={{opacity:fade,overflow:'hidden'}}>
  <OffthreadVideo src={staticFile(src)} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/>
  <AbsoluteFill style={{background:'linear-gradient(180deg,rgba(4,24,30,.26),rgba(4,24,30,.05) 40%,rgba(4,24,30,.62) 100%)'}}/>
 </AbsoluteFill>;
};
const Reel:React.FC<Props> = ({voiceFrames,introFrames,outroFrames,logo,logoBackground,photos,captions,mare,musa}) => <AbsoluteFill style={{background:'#071a20'}}>
 <Sequence from={0} durationInFrames={introFrames}><Logo src={logo} bg={logoBackground} duration={introFrames} ending={false}/></Sequence>
 <Sequence from={introFrames} durationInFrames={voiceFrames}>
  {photos.map((p,i)=><Sequence key={p.src+i} from={p.from} durationInFrames={p.duration}><MovingPhoto photo={p} index={i}/></Sequence>)}
  <Sequence from={0} durationInFrames={150}><VideoInsert src={mare} duration={150}/></Sequence>
  <Sequence from={744} durationInFrames={140}><VideoInsert src={musa} duration={140}/></Sequence>
  <AbsoluteFill style={{border:'2px solid rgba(245,220,172,.16)',margin:30,width:'calc(100% - 60px)',height:'calc(100% - 60px)',pointerEvents:'none'}} />
  <Sequence from={0} durationInFrames={100}><Title/></Sequence>
  <Captions captions={captions}/>
 </Sequence>
 <Sequence from={introFrames+voiceFrames} durationInFrames={outroFrames}><Logo src={logo} bg={logoBackground} duration={outroFrames} ending={true}/></Sequence>
</AbsoluteFill>;
const defaults:Props={durationInFrames:90,voiceFrames:30,introFrames:30,outroFrames:30,logo:'',logoBackground:'#0b2830',photos:[],captions:[],mare:'',musa:''};
const Root:React.FC=()=> <Composition id="KoraCinema" component={Reel} durationInFrames={90} fps={30} width={1080} height={1920} defaultProps={defaults} calculateMetadata={({props})=>({durationInFrames:props.durationInFrames})}/>;
registerRoot(Root);
