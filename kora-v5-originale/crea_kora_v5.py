#!/usr/bin/env python3
"""Crea una bozza KORA separata con TypingCamera e AnimatedUnderline originali V5."""
import hashlib,json,os,shutil,subprocess,sys,tempfile,uuid
from pathlib import Path
from PIL import ImageFont

BASE=Path.home()/'Desktop'/'SKILL FRANCESCO'/'PRODUZIONE_VIDEO'
REEL=BASE/'videocodex-mac'/'reels'/'kora'
SOURCE=REEL/'output-kora-artistico'/'bozza-kora-artistico.mp4'
OUTPUT=REEL/'output-kora-v5-originale'
PROJECT=BASE/'premium-v5-mac'/'GONDAR_FINAL'
HERE=Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def probe(tool,path):
    return json.loads(subprocess.check_output([tool,'-v','error','-show_streams','-show_format','-of','json',str(path)]))
def main():
    sys.path.insert(0,str(BASE/'videocodex-mac'/'tools'))
    import salento_tools as st
    ffmpeg,ffprobe=st.tool(st.config(),'ffmpeg'),st.tool(st.config(),'ffprobe')
    remotion=PROJECT/'node_modules'/'.bin'/'remotion'; entry=HERE/'KoraV5Entry.tsx'; font=PROJECT/'public'/'arialbd.ttf'
    for p in [SOURCE,remotion,entry,font,PROJECT/'src/premium-v5/typography.tsx',PROJECT/'src/v3/index.ts']:
        if not p.is_file():raise ValueError('File mancante: '+str(p))
    if OUTPUT.exists():raise ValueError('output-kora-v5-originale esiste già: non sovrascrivo.')
    before=sha(SOURCE); metadata=probe(ffprobe,SOURCE)
    vs=[s for s in metadata['streams'] if s['codec_type']=='video']; au=[s for s in metadata['streams'] if s['codec_type']=='audio']
    if len(vs)!=1 or len(au)!=1 or vs[0].get('width')!=1080 or vs[0].get('height')!=1920 or vs[0].get('r_frame_rate')!='30/1' or abs(float(metadata['format']['duration'])-1598/30)>.3:
        raise ValueError('La bozza artistica non ha formato o durata attesi.')
    text='KORA · POLICORO'; fontface=ImageFont.truetype(str(font),72); total=fontface.getlength(text); events=[]; glyphs=[]
    for i,ch in enumerate(text):
        ident='kora-v5-char-%02d'%i
        events.append({'id':ident,'frame':8+i*3,'component':'TypingCamera','phase':'character'})
        glyphs.append({'char':ch,'cue':ident,'word':0,'line':0,'x':fontface.getlength(text[:i]),'width':fontface.getlength(ch)})
    left=round((1080-total)/2)
    if left<70:raise ValueError('Il titolo non entra nella zona sicura.')
    token=uuid.uuid4().hex; static=PROJECT/'public'/('kora-v5-'+token); src=PROJECT/'src'/('kora-v5-'+token)
    work=Path(tempfile.mkdtemp(prefix='kora-v5-',dir=str(REEL)))
    try:
        static.mkdir(parents=True);src.mkdir()
        video=static/'artistico.mp4'
        try:os.link(SOURCE,video)
        except OSError:shutil.copy2(SOURCE,video)
        shutil.copy2(entry,src/'index.tsx')
        props={'source':video.relative_to(PROJECT/'public').as_posix(),'director':{'fps':30,'durationInFrames':120,'events':events},'glyphs':glyphs,'left':left}
        propsfile=work/'props.json';propsfile.write_text(json.dumps(props,ensure_ascii=False),encoding='utf8')
        silent=work/'video-senza-audio.mp4'; result=work/'bozza-kora-v5-originale.mp4'
        cmd=[str(remotion),'render',str(src/'index.tsx'),'KoraV5Originale',str(silent),'--props',str(propsfile),'--codec=h264','--concurrency=1']
        if os.environ.get('REMOTION_BROWSER_EXECUTABLE'):cmd+=['--browser-executable',os.environ['REMOTION_BROWSER_EXECUTABLE']]
        print('Creo la bozza V5: il rendering può richiedere diversi minuti. Lascia aperto il Terminale.',flush=True)
        subprocess.run(cmd,cwd=PROJECT,check=True)
        print('Copio l’audio della bozza artistica senza ricodifica...',flush=True)
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(silent),'-i',str(SOURCE),'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',str(result)],check=True)
        out=probe(ffprobe,result); outvs=[s for s in out['streams'] if s['codec_type']=='video']; outaud=[s for s in out['streams'] if s['codec_type']=='audio']
        if len(outvs)!=1 or len(outaud)!=1 or abs(float(out['format']['duration'])-float(metadata['format']['duration']))>.3 or sha(SOURCE)!=before:raise ValueError('Verifica finale durata, tracce o integrità della fonte non riuscita.')
        report={'fonte':str(SOURCE),'fonte_sha256':before,'output_sha256':sha(result),'durata_secondi':out['format']['duration'],'componenti_originali':['TypingCamera','AnimatedUnderline'],'note':['Audio della bozza artistica copiato senza ricodifica; nessun nuovo SFX V5 aggiunto.','Video ricodificato: controllare qualità, titoli, leggibilità, sincronizzazione e orari.','Non è una verifica della pipeline V5 completa.']}
        OUTPUT.mkdir(); shutil.move(str(result),str(OUTPUT/'bozza-kora-v5-originale.mp4'))
        (OUTPUT/'verifica.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print('\nFATTO:',OUTPUT/'bozza-kora-v5-originale.mp4');print('Le bozze precedenti sono intatte. Rivedi e ascolta la nuova versione.')
    finally:
        shutil.rmtree(static,ignore_errors=True);shutil.rmtree(src,ignore_errors=True);shutil.rmtree(work,ignore_errors=True)
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:sys.exit('ERRORE: '+str(e)+'\nLe bozze precedenti non sono state modificate. Chiedi assistenza.')
