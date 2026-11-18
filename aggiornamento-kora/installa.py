"""Installa il supporto KORA nella versione di VIDEOCODEX già distribuita.
Non modifica copione, preparazione, voce, mix, immagini o progetti Reel.
"""
import hashlib
import os
from pathlib import Path
import shutil
import sys

ORIGINAL_ROOT = 'c822c89d696c3a87e7dba12dcbf65adee84d40da3450b980e62ffd9fc2e83fbe'
SOURCE = Path(__file__).resolve().parent / 'files'


def install(root):
    root = root.resolve()
    current = root / 'GONDAR_FINAL' / 'src' / 'Root.tsx'
    destinations = {
        'Root.tsx': current,
        'KoraReel.tsx': root / 'GONDAR_FINAL' / 'src' / 'reels' / 'KoraReel.tsx',
        'kora_foto.py': root / 'tools' / 'kora_foto.py',
    }
    if not (root / 'config.json').is_file() or not current.is_file():
        raise ValueError('Indica la cartella videocodex-mac corretta')
    if hashlib.sha256(current.read_bytes()).hexdigest() != ORIGINAL_ROOT:
        raise ValueError('Root.tsx è diverso dalla versione attesa: non sovrascrivo modifiche')
    if any(destinations[name].exists() for name in ('KoraReel.tsx', 'kora_foto.py')):
        raise ValueError('Aggiornamento già presente oppure file con lo stesso nome: non sovrascrivo')
    for name in destinations:
        if not (SOURCE / name).is_file():
            raise ValueError('File aggiornamento mancante: ' + name)
    backup = root / 'backup-installazione-kora'
    if backup.exists():
        raise ValueError('Il backup esiste già: non sovrascrivo')
    backup.mkdir()
    shutil.copy2(current, backup / 'Root.tsx')
    written = []
    try:
        for name, target in destinations.items():
            temp = target.with_name(target.name + '.kora-tmp')
            if temp.exists():
                raise ValueError('File temporaneo esistente: ' + str(temp))
            shutil.copy2(SOURCE / name, temp)
            os.replace(temp, target)
            written.append(name)
    except Exception:
        if 'Root.tsx' in written:
            shutil.copy2(backup / 'Root.tsx', current)
        for name in ('KoraReel.tsx', 'kora_foto.py'):
            if name in written:
                destinations[name].unlink()
        raise
    print('Aggiornamento KORA installato. Voce, mix e progetti non sono stati modificati.')
    print('Backup della configurazione Remotion:', backup)


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Uso: python installa.py percorso-della-cartella-videocodex-mac')
        install(Path(sys.argv[1]))
    except (ValueError, OSError) as error:
        sys.exit('ERRORE: ' + str(error))
