#!/usr/bin/env python3
"""Bozza cinematografica KORA con clip locali e musica CC0. Non tocca le altre bozze."""
import hashlib, json, os, shutil, subprocess, sys, tempfile, uuid
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path.home() / 'Desktop' / 'SKILL FRANCESCO' / 'PRODUZIONE_VIDEO' / 'videocodex-mac'
REEL = ROOT / 'reels' / 'kora'
PHOTOS = ROOT.parent / 'FOTO REEL'
PROJECT = ROOT / 'GONDAR_FINAL'
SOURCE = REEL / 'output-kora-effetti' / 'bozza-kora-effetti.mp4'
OUTPUT = REEL / 'output-kora-cinema'
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
    required=[remotion,SOURCE,HERE/'CinemaEntry.tsx',HERE/'mare.mp4',HERE/'musa.mp4',HERE/'musica-next-to-you.mp3']
    missing=[str(x) for x in required if not x.is_file()]
    if missing: raise ValueError('File mancanti: '+', '.join(missing))
    if OUTPUT.exists(): raise ValueError('output-kora-cinema esiste già: non sovrascrivo il lavoro precedente.')
    if sha(HERE/'musica-next-to-you.mp3')!='95d620e1ad7bd7c73366979e384f172be21ebc5fe68bdc1af3908faf8a7c7b44':
        raise ValueError('Il file musicale non corrisponde a quello verificato.')
    timeline,captions,logo,photos=kf.preflight(REEL,PHOTOS)
    kora=[c for c in captions if c['text'].strip(' .,!?').casefold()=='kora']
    if len(kora)!=2: raise ValueError('Non trovo entrambi i sottotitoli KORA corretti: controllare il progetto.')
    metadata=probe(ffprobe,SOURCE)
    vs=[s for s in metadata['streams'] if s['codec_type']=='video']
    aud=[s for s in metadata['streams'] if s['codec_type']=='audio']
    if len(vs)!=1 or len(aud)!=1 or vs[0].get('r_frame_rate')!='30/1' or abs(float(metadata['format']['duration'])-1598/30)>.3:
        raise ValueError('La bozza con effetti non ha il formato o la durata attesi.')
    for name,minimum in [('mare.mp4',5),('musa.mp4',140/30)]:
        clip=probe(ffprobe,HERE/name)
        if not any(s['codec_type']=='video' and float(s.get('duration',0))>=minimum for s in clip['streams']):
            raise ValueError('Il video '+name+' è troppo corto o illeggibile.')
    token=uuid.uuid4().hex
    static=PROJECT/'public'/'kora-cinema'/token
    src=PROJECT/'src'/('kora-cinema-'+token)
    work=Path(tempfile.mkdtemp(prefix='kora-cinema-',dir=str(REEL)))
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
        for filename in ['mare.mp4','musa.mp4']: shutil.copy2(HERE/filename,static/filename)
        shutil.copy2(HERE/'CinemaEntry.tsx',src/'index.tsx')
        props={'durationInFrames':1598,'voiceFrames':1478,'introFrames':60,'outroFrames':60,
               'logo':(static/'logo.png').relative_to(PROJECT/'public').as_posix(),
               'logoBackground':kf.bg_for_logo(logo),'photos':items,'captions':captions,
               'mare':(static/'mare.mp4').relative_to(PROJECT/'public').as_posix(),
               'musa':(static/'musa.mp4').relative_to(PROJECT/'public').as_posix()}
        propfile=work/'props.json'; propfile.write_text(json.dumps(props,ensure_ascii=False),encoding='utf-8')
        silent=work/'senza-audio.mp4'; stem=work/'MUSICA.wav'; result=work/'bozza-kora-cinema.mp4'
        cmd=[str(remotion),'render',str(src/'index.tsx'),'KoraCinema',str(silent),'--props',str(propfile),'--concurrency=1','--codec=h264']
        if os.environ.get('REMOTION_BROWSER_EXECUTABLE'): cmd+=['--browser-executable',os.environ['REMOTION_BROWSER_EXECUTABLE']]
        print('Creo il video: lascia aperto il Terminale, può richiedere diversi minuti...',flush=True)
        run(cmd,cwd=PROJECT)
        print('Preparo la traccia musicale separata e il mix con voce ed effetti...',flush=True)
        run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(HERE/'musica-next-to-you.mp3'),
             '-af','atrim=duration=53.266667,asetpts=PTS-STARTPTS,volume=-12dB,afade=t=in:st=0:d=1,afade=t=out:st=51.266667:d=2',
             '-ar','48000','-ac','2','-c:a','pcm_s16le',str(stem)])
        run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(silent),'-i',str(SOURCE),'-i',str(stem),
             '-filter_complex','[1:a]volume=-0.5dB[voice];[voice][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.75:level=0:latency=1[a]',
             '-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(result)])
        out=probe(ffprobe,result); outvs=[s for s in out['streams'] if s['codec_type']=='video']; outaud=[s for s in out['streams'] if s['codec_type']=='audio']
        if len(outvs)!=1 or len(outaud)!=1 or abs(float(out['format']['duration'])-float(metadata['format']['duration']))>.3:
            raise ValueError('La verifica della durata o delle tracce non è riuscita.')
        measured=run([ffmpeg,'-hide_banner','-i',str(result),'-af','loudnorm=I=-16:TP=-1.8:LRA=11:print_format=json','-f','null',os.devnull],capture_output=True,text=True).stderr
        loud=json.loads(measured[measured.rfind('{'):measured.rfind('}')+1])
        report={'fonte_audio':str(SOURCE),'fonte_audio_sha256':sha(SOURCE),'output_sha256':sha(result),
                'durata_secondi':out['format']['duration'],'musica':'Next to You — Joth, CC0 1.0',
                'fonte_musica':'https://opengameart.org/content/next-to-you', 'musica_originale_sha256':sha(HERE/'musica-next-to-you.mp3'),
                'livello_musica_db':-12,'riduzione_mix_voce_sfx_db':-0.5,'loudness':loud,
                'clip':[{'file':x,'sha256':sha(HERE/x)} for x in ['mare.mp4','musa.mp4']],
                'note':['Video delle clip senza l’audio originale. La voce e gli effetti sono rimissati con musica, limiter e ricodifica AAC.',
                        'Controllare sincronizzazione, volume e rappresentatività della scena serale.',
                        'Musa dichiarata generata con IA. Nessuna ripresa drone.']}
        OUTPUT.mkdir()
        shutil.move(str(result),str(OUTPUT/'bozza-kora-cinema.mp4')); shutil.move(str(stem),str(OUTPUT/'MUSICA.wav'))
        (OUTPUT/'verifica.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('\nFATTO:',OUTPUT/'bozza-kora-cinema.mp4')
        print('Musica separata:',OUTPUT/'MUSICA.wav')
        print('Misure LUFS / dBTP:',loud['input_i'],loud['input_tp'])
        print('Le bozze precedenti sono intatte. Rivedi e ascolta la nuova versione prima di pubblicarla.')
    finally:
        shutil.rmtree(static,ignore_errors=True); shutil.rmtree(src,ignore_errors=True); shutil.rmtree(work,ignore_errors=True)

if __name__=='__main__':
    try: main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        sys.exit('ERRORE: %s\nLe bozze precedenti non sono state modificate. Chiedi assistenza.'%e)
