#!/usr/bin/env python3
"""Nuova bozza artistica KORA: non modifica le versioni precedenti."""
import hashlib, json, os, shutil, subprocess, sys, tempfile, uuid
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path.home() / 'Desktop' / 'SKILL FRANCESCO' / 'PRODUZIONE_VIDEO' / 'videocodex-mac'
REEL = ROOT / 'reels' / 'kora'
PHOTOS = ROOT.parent / 'FOTO REEL'
PROJECT = ROOT / 'GONDAR_FINAL'
SOURCE = REEL / 'output-kora-cinema' / 'bozza-kora-cinema.mp4'
OUTPUT = REEL / 'output-kora-artistico'
ASSETS = ROOT.parent / 'kora-cinema'
HERE = Path(__file__).resolve().parent


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def probe(tool,path):
    return json.loads(subprocess.check_output([tool,'-v','error','-show_streams','-show_format','-of','json',str(path)]))

def main():
    sys.path.insert(0,str(ROOT/'tools'))
    import kora_foto as kf
    import salento_tools as st
    ffmpeg,ffprobe=st.tool(st.config(),'ffmpeg'),st.tool(st.config(),'ffprobe')
    remotion=PROJECT/'node_modules'/'.bin'/'remotion'
    required=[remotion,SOURCE,HERE/'ArtisticoEntry.tsx',ASSETS/'mare.mp4',ASSETS/'musa.mp4']
    missing=[str(x) for x in required if not x.is_file()]
    if missing: raise ValueError('File mancanti: '+', '.join(missing))
    if OUTPUT.exists(): raise ValueError('output-kora-artistico esiste già: non sovrascrivo il lavoro precedente.')
    timeline,captions,logo,photos=kf.preflight(REEL,PHOTOS)
    kora=[c for c in captions if c['text'].strip(' .,!?').casefold()=='kora']
    if len(kora)!=2: raise ValueError('Non trovo entrambi i sottotitoli KORA corretti: controllare il progetto.')
    metadata=probe(ffprobe,SOURCE)
    vs=[s for s in metadata['streams'] if s['codec_type']=='video']
    aud=[s for s in metadata['streams'] if s['codec_type']=='audio']
    if len(vs)!=1 or len(aud)!=1 or vs[0].get('r_frame_rate')!='30/1' or abs(float(metadata['format']['duration'])-1598/30)>.3:
        raise ValueError('La bozza con effetti non ha il formato o la durata attesi.')
    for name,minimum in [('mare.mp4',5),('musa.mp4',140/30)]:
        clip=probe(ffprobe,ASSETS/name)
        if not any(s['codec_type']=='video' and float(s.get('duration',0))>=minimum for s in clip['streams']):
            raise ValueError('Il video '+name+' è troppo corto o illeggibile.')
    token=uuid.uuid4().hex
    static=PROJECT/'public'/'kora-artistico'/token
    src=PROJECT/'src'/('kora-artistico-'+token)
    work=Path(tempfile.mkdtemp(prefix='kora-artistico-',dir=str(REEL)))
    try:
        static.mkdir(parents=True); src.mkdir()
        with Image.open(logo) as img: ImageOps.exif_transpose(img).convert('RGBA').save(static/'logo.png')
        items=[]
        for i,file in enumerate(photos):
            dest=static/('foto-%02d.jpg'%(i+1))
            with Image.open(file) as img:
                image=ImageOps.exif_transpose(img).convert('RGB'); image.thumbnail((2160,2160),Image.Resampling.LANCZOS); image.save(dest,quality=90)
            duration=min(kf.CUTS[-1]-kf.CUTS[i],kf.CUTS[i+1]-kf.CUTS[i]+(12 if i<7 else 0))
            items.append({'src':dest.relative_to(PROJECT/'public').as_posix(),'from':kf.CUTS[i],'duration':duration})
        print('Preparo il grandangolo sulla clip del mare...',flush=True)
        run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(ASSETS/'mare.mp4'),
             '-vf','crop=432:768,lenscorrection=cx=0.5:cy=0.5:k1=-0.28:k2=-0.06,scale=540:960,crop=432:768',
             '-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',str(static/'mare.mp4')])
        shutil.copy2(ASSETS/'musa.mp4',static/'musa.mp4')
        shutil.copy2(HERE/'ArtisticoEntry.tsx',src/'index.tsx')
        props={'durationInFrames':1598,'voiceFrames':1478,'introFrames':60,'outroFrames':60,
               'logo':(static/'logo.png').relative_to(PROJECT/'public').as_posix(),
               'logoBackground':kf.bg_for_logo(logo),'photos':items,'captions':captions,
               'mare':(static/'mare.mp4').relative_to(PROJECT/'public').as_posix(),
               'musa':(static/'musa.mp4').relative_to(PROJECT/'public').as_posix()}
        propfile=work/'props.json'; propfile.write_text(json.dumps(props,ensure_ascii=False),encoding='utf-8')
        silent=work/'senza-audio.mp4'; result=work/'bozza-kora-artistico.mp4'
        cmd=[str(remotion),'render',str(src/'index.tsx'),'KoraArtistico',str(silent),'--props',str(propfile),'--concurrency=1','--codec=h264']
        if os.environ.get('REMOTION_BROWSER_EXECUTABLE'): cmd+=['--browser-executable',os.environ['REMOTION_BROWSER_EXECUTABLE']]
        print('Creo il video: lascia aperto il Terminale, può richiedere diversi minuti...',flush=True)
        run(cmd,cwd=PROJECT)
        print('Aggiungo l’audio della bozza cinema senza ricodificarlo...',flush=True)
        run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(silent),'-i',str(SOURCE),
             '-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',str(result)])
        out=probe(ffprobe,result); outvs=[s for s in out['streams'] if s['codec_type']=='video']; outaud=[s for s in out['streams'] if s['codec_type']=='audio']
        if len(outvs)!=1 or len(outaud)!=1 or abs(float(out['format']['duration'])-float(metadata['format']['duration']))>.3:
            raise ValueError('La verifica della durata o delle tracce non è riuscita.')
        report={'fonte_audio':str(SOURCE),'fonte_audio_sha256':sha(SOURCE),'output_sha256':sha(result),
                'durata_secondi':out['format']['duration'],'video':outvs[0], 'audio':outaud[0],
                'clip':[{'file':x,'sha256':sha(ASSETS/x)} for x in ['mare.mp4','musa.mp4']],
                'note':['Titolo The Art of Being nel logo iniziale; distorsione lente sul mare; spioncino temporaneo sulla Musa.',
                        'Audio della bozza cinema copiato senza ricodifica; rivedere musica, sottotitoli e sincronizzazione.',
                        'Musa dichiarata generata con IA. Nessuna ripresa drone.']}
        OUTPUT.mkdir()
        shutil.move(str(result),str(OUTPUT/'bozza-kora-artistico.mp4'))
        (OUTPUT/'verifica.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('\nFATTO:',OUTPUT/'bozza-kora-artistico.mp4')
        print('Le bozze precedenti sono intatte. Rivedi la nuova versione prima di pubblicarla.')
    finally:
        shutil.rmtree(static,ignore_errors=True); shutil.rmtree(src,ignore_errors=True); shutil.rmtree(work,ignore_errors=True)

if __name__=='__main__':
    try: main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        sys.exit('ERRORE: %s\nLe bozze precedenti non sono state modificate. Chiedi assistenza.'%e)
