#!/usr/bin/env python3
"""Verifica isolata del compilatore e mixer V5 con soli suoni sintetici temporanei."""
import hashlib, importlib.util, json, math, os, shutil, subprocess, sys, tempfile, wave
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def run():
    try:
        import numpy as np
    except ImportError:
        raise ValueError('Manca numpy nell’ambiente Python attivo. Comunica questo messaggio per assistenza.')
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise ValueError('Non trovo ffmpeg. Usa lo stesso Terminale con cui hai creato KORA.')
    spec=importlib.util.spec_from_file_location('premium_tools_originale', ROOT/'scripts/premium_tools.py')
    premium=importlib.util.module_from_spec(spec); spec.loader.exec_module(premium)
    st=premium.st
    with tempfile.TemporaryDirectory(prefix='v5-audio-test-') as d:
        root=Path(d); lib=root/'suoni-sintetici'; lib.mkdir(); voice=root/'voce-test.wav'; effect=lib/'click-test.wav'; catalog=lib/'audio_catalog.json'
        def wav(path,x):
            pcm=np.clip(x,-1,1); pcm=(pcm*32767).astype('<i2')
            with wave.open(str(path),'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(pcm.tobytes())
        t=np.arange(96000)/48000
        wav(voice,0.09*np.sin(2*np.pi*220*t))
        x=np.zeros(4800); x[720:744]=np.hanning(24)*0.6; wav(effect,x)
        original=st.digest(voice); fxhash=st.digest(effect)
        # This authorization applies ONLY to the generated synthetic fixture in this temporary folder.
        entry={'path':'click-test.wav','sha256':fxhash,'durationSeconds':.1,'status':'AVAILABLE','licenseStatus':'LICENSE_VERIFIED','commercialUse':'ALLOWED'}
        catalog.write_text(json.dumps({'assets':[entry]}),encoding='utf8')
        config={'_root':root,'_paths':{'audioLibrary':lib,'audioCatalog':catalog},'runtime':{'ffmpeg':ffmpeg},'requiredComponents':['TypingCamera']}
        manifest={'fps':30,'durationInFrames':60,'events':[{'id':'test-click','frame':30,'component':'TypingCamera','phase':'character','sound':{'path':'click-test.wav','sourcePeakMs':15,'maxDurationSeconds':.1,'peakDbFS':-24,'fadeInMs':1,'fadeOutMs':2}}]}
        cue=st.compile_cues(config,manifest); item=cue['events'][0]['audio']
        assert item['targetSample']==48000 and item['startSample']+item['peakSample']==48000
        # An unapproved or changed file must never be accepted.
        catalog.write_text(json.dumps({'assets':[{**entry,'licenseStatus':'UNKNOWN'}]}),encoding='utf8')
        try: st.compile_cues(config,manifest)
        except ValueError as e:
            if 'rights unavailable' not in str(e): raise
        else: raise AssertionError('Protezione diritti non funzionante')
        catalog.write_text(json.dumps({'assets':[entry]}),encoding='utf8')
        output=root/'mix-di-test'; premium.mix(config,cue,voice,output)
        for name in ['VOICEOVER_STEM.wav','SFX_STEM.wav','MIX.wav','mix-audit.json']:
            assert (output/name).is_file(), 'File di test mancante: '+name
        before=premium.decode(config,voice); after=premium.decode(config,output/'VOICEOVER_STEM.wav')
        assert before.shape==after.shape and np.max(np.abs(before-after))<1e-6
        assert st.digest(voice)==original and st.digest(effect)==fxhash
        audit=json.loads((output/'mix-audit.json').read_text(encoding='utf8'))
        assert audit['music'] is False and audit['cueCount']==1
        try: premium.mix(config,cue,voice,output)
        except ValueError as e:
            if 'Choose a new mix output folder' not in str(e): raise
        else: raise AssertionError('Protezione sovrascrittura non funzionante')
    print('OK: cue allineato, diritti verificati su un suono sintetico, voce invariata, stem separati, blocco sovrascrittura.')
    print('Test temporaneo eliminato. Nessun audio reale o bozza KORA è stato letto o modificato.')
    print('VERIFICA AUDIO SINTETICA COMPLETATA.')

if __name__=='__main__':
    try: run()
    except (ValueError,AssertionError,OSError,subprocess.SubprocessError) as e:
        sys.exit('ERRORE: '+str(e)+'\nComunica questo messaggio per assistenza. Le bozze KORA non sono state modificate.')
