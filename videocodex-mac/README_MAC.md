# VIDEOCODEX Mac — pipeline sperimentale

Base ricostruita da zero, ispirata alla Skill Premium V5: **non è il codice originale** e non replica ancora tutti i suoi effetti. Funziona a fasi: testo → prompt e scene → voce ElevenLabs o audio fornito → caption locali → mix → MP4 verticale. L'output va controllato prima della pubblicazione.

## Cosa è automatico e cosa no

- Automatico: divisione indicativa del testo in massimo sei scene, bozze di prompt, trascrizione parola per parola, stima dei cambi scena, mix voce e un eventuale SFX ai cambi, sottotitoli, montaggio e misurazione audio dell'MP4.
- Manuale: scrivere e controllare il testo; generare/scaricare le clip con un servizio esterno; verificare licenze, contenuto, caption e tempi. I prompt sono bozze, non una garanzia di immagini corrette. Non spacciare immagini AI per riprese documentarie autentiche. Senza clip il render normale si ferma.
- Ancora incompleto: generazione automatica di un copione affidabile da un semplice tema, generazione automatica delle clip, regia completa di effetti/suoni V5 e SFX del typing. Non è un workflow completamente automatico dal tema fino alla pubblicazione.
- Il test di integrazione è stato eseguito con audio e clip sintetici in un ambiente Linux, **non sul tuo Mac/OpenCore**; ElevenLabs e Whisper con voce reale non sono stati testati in questo ambiente. Compatibilità, tempi ed effetti sul tuo Mac sono da verificare.

## 1. Installazione

Scarica ed estrai la cartella `videocodex-mac`. Il pacchetto non è stato caricato automaticamente sul tuo Drive. Installa [Homebrew](https://brew.sh/) se necessario, poi in Terminale:

```bash
brew install node python ffmpeg
```

Scrivi `cd ` in Terminale, trascina la cartella `videocodex-mac` nella finestra e premi Invio. Poi:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install numpy pillow edge-tts faster-whisper
cd GONDAR_FINAL
npm ci
cd ..
python tools/salento_tools.py verify
```

`verify` controlla solo la presenza di percorsi e strumenti, non la qualità del video. Riaprendo Terminale, ritorna nella cartella e riattiva `source .venv/bin/activate`. Il progetto trova la propria cartella automaticamente; `BENVENUTI_SALENTO_ROOT` può indicarne un'altra.

Con il tuo Intel i5 e 16 GB è consigliato partire da una prova breve: Whisper usa il modello `base` su CPU e il rendering usa un solo processo. Entrambi possono essere lenti. Il primo avvio di Whisper scarica il modello e il render Remotion può scaricare un browser compatibile; è richiesta una connessione. Se una dipendenza o il browser non funziona su OpenCore, serve valutare l'errore specifico.

## 2. Crea un progetto

Crea un file di solo testo `testo.txt` nella cartella principale con il copione già revisionato. Per esempio:

```bash
python tools/pipeline.py init --script testo.txt --dir reels/mio-reel --title "Il mio titolo"
```

Il comando crea una cartella nuova (non sovrascrive una precedente), con `script.txt`, `scenes.json`, `prompts.md` e `clips/`. I prompt sono divisi per scena: migliorali, genera le clip nel tuo servizio video e salvale in `reels/mio-reel/clips/` con i nomi indicati (`clip-01.mp4` ecc.). Ogni clip deve essere un MP4 senza necessità di audio; l'audio delle clip viene disattivato. Se una clip è più corta della scena, viene ripetuta. Per cambiare il testo del copione è meglio creare un progetto nuovo: i testi delle scene devono corrispondere allo script.

## 3. Prepara voce e sottotitoli

### Opzione semplice: scarica la voce da ElevenLabs

Genera la voce nell'interfaccia ElevenLabs e scarica l'audio sul Mac. Senza condividere password o chiavi, trascina il file sul Terminale per inserirne il percorso dopo `--voice`. Esempio:

```bash
python tools/pipeline.py prepare --dir reels/mio-reel --voice ~/Downloads/voce.mp3
```

Il comando converte l'audio senza cambiare la velocità, allinea le parole con faster-whisper e crea `prepared/`. Controlla manualmente `prepared/captions.json`: Whisper può sbagliare parole e orari. Controlla anche i cambi scena in `prepared/timeline.json`: sono stime proporzionali, non una regia semantica. Non modificare i frame delle scene senza aggiornare anche il director.

### Opzione API ElevenLabs (facoltativa)

Solo se vuoi generare la voce direttamente dalla pipeline: nell'account ElevenLabs crea una chiave API con permessi minimi e copia il Voice ID della voce desiderata. **Non inviare la chiave in chat e non inserirla in file del progetto.** Nell'attuale finestra Terminale (l'input della chiave rimane nascosto):

```bash
read -rs -p 'Chiave API ElevenLabs: ' ELEVENLABS_API_KEY; echo
export ELEVENLABS_API_KEY
read -r -p 'Voice ID ElevenLabs: ' ELEVENLABS_VOICE_ID
export ELEVENLABS_VOICE_ID
python tools/pipeline.py prepare --dir reels/mio-reel --elevenlabs
unset ELEVENLABS_API_KEY ELEVENLABS_VOICE_ID
```

Questo invia lo script a ElevenLabs e può consumare crediti; verifica piano, prezzi, privacy e diritti. Non eseguirlo finché non sei pronto. L'audio originale ricevuto è conservato in `prepared/`. Per un modello diverso usa `--eleven-model`; controlla che sia disponibile per il tuo account.

In entrambi i casi `prepared/` non viene sovrascritta. Se qualcosa fallisce o vuoi rifare la voce, conserva/rinomina la cartella incompleta prima di riprovare. Puoi usare `--captions percorso.json` per fornire caption già revisionate invece di Whisper. Le librerie Python vanno installate nel venv.

## 4. SFX facoltativo ai cambi scena

Il sistema non inventa suoni o diritti. Aggiungi un SFX breve in `AUDIO_LIBRARY/`, poi:

```bash
python tools/salento_tools.py scan-audio
```

Nel catalogo `AUDIO_LIBRARY/audio_catalog.json`, solo dopo aver verificato licenza, eventuale attribuzione e uso consentito, annota la prova in `licenseEvidence` e imposta per quel file `licenseStatus` a `USER_CONFIRMED` e `commercialUse` a `AUTHORIZED`. Il cambio di contenuto del file richiede una nuova verifica. Per usarlo nel comando `prepare` aggiungi, ad esempio, `--transition-sfx whoosh/nome.wav` (percorso relativo alla libreria). La preparazione è immutabile: l'opzione va scelta prima di preparare, oppure occorre rifare `prepared/`. Il sistema applica un suono ai cambi scena, non al primo titolo né a ogni lettera. Controlla sempre la sincronizzazione e i livelli. Senza SFX il mix ha solo la voce e uno stem SFX silenzioso.

## 5. Rivedi ed esporta

Dopo aver controllato voce, `captions.json`, scene, contenuti e diritti delle clip:

```bash
python tools/pipeline.py render --dir reels/mio-reel --reviewed
```

Il risultato è `reels/mio-reel/output/reel.mp4`. `output/qa.json` contiene metadata e misura loudness del file finale: controlla anche ascolto, sincronizzazione, livelli, formato e attribuzioni richieste. Le props di output sono un registro tecnico e non sono riutilizzabili dopo la pulizia dei file temporanei. Stem separati e mix si trovano in `prepared/mix/`; niente musica incorporata. `output/` non viene sovrascritta, anche se un render fallisce: conserva/rinomina la cartella precedente prima di riprovare.

Per una bozza con sfondi segnaposto invece delle clip mancanti aggiungi `--allow-placeholders`; non è un Reel pronto per la pubblicazione. Per vedere solo la vecchia demo grafica: `cd GONDAR_FINAL && npm run dev`, quindi seleziona `DemoSalento`; è muta e non usa i file del tuo progetto.

## Specifiche e limiti creativi

Vedi `FORMAT.md`. La versione automatica usa titolo typing, sfondi/clip e caption; non include ancora tutta la regia originale Premium V5. Il render può essere sensibilmente lento su Mac del 2012, e non è garantito che tutti i servizi o i pacchetti supportino la configurazione OpenCore.
