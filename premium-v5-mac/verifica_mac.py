#!/usr/bin/env python3
"""Verifica locale della copia V5: non accede a Reel, Drive o cataloghi audio."""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
project=root/'GONDAR_FINAL'

def main():
    manifest=json.loads((root/'hash-originali.json').read_text(encoding='utf8'))
    for rel, expected in manifest.items():
        p=root/rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise ValueError('Il file originale è assente o modificato: '+rel)
    npm=shutil.which('npm')
    if not npm: raise ValueError('Non trovo npm. Apri il Terminale usato per il progetto videocodex-mac e riprova.')
    if not (project/'node_modules'/'typescript'/'bin'/'tsc').is_file():
        print('Installo le dipendenze nella sola cartella premium-v5-mac; serve una connessione Internet.',flush=True)
        subprocess.run([npm,'ci','--no-audit','--no-fund'],cwd=project,check=True)
    print('Verifico TypeScript, import dei componenti e funzioni numeriche...',flush=True)
    subprocess.run([npm,'run','verifica'],cwd=project,check=True)
    print('\nVERIFICA COMPLETATA. Le bozze KORA non sono state modificate.')
    print('Questo controllo non produce video e non certifica l’intera produzione V5 sul Mac.')

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        sys.exit('ERRORE: '+str(exc)+'\nNessuna bozza KORA è stata modificata. Comunica questo messaggio per assistenza.')
