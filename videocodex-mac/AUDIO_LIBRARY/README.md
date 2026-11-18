# AUDIO_LIBRARY

Effetti sonori (SFX) per i Reel. Organizza i file in sottocartelle per funzione:

- `whoosh/` — transizioni e movimenti di camera
- `click/` — typing, UI, pulsanti
- `impact/` — bass hit, colpi, impatti
- `shutter/` — scatti fotografici
- `tick/` — date, conteggi, orologi
- `sweep/` — maschere e reveal
- `accent/` — accenti su CTA e parole chiave
- `gear/` — meccanismi, tragitto, data

## Regole
- Solo file con **licenza chiara** (Freesound con attribuzione, Pixabay, registrazioni proprie, ecc.)
- Niente musica: la libreria contiene **solo SFX brevi** (di norma < 2 s)
- Dopo aver aggiunto file, lancia `python3 tools/salento_tools.py scan-audio`
- I file nuovi sono `UNKNOWN`: conferma i diritti nel `audio_catalog.json` prima di usarli nei cue
- Mai usare un file senza averne verificato la licenza: l'autorizzazione di un file non si estende agli altri
