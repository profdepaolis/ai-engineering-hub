# Format Reel — obiettivi per la ricostruzione Mac

Il riferimento è la Skill `benvenuti-salento-premium-edit`; gli effetti originali non sono disponibili. Questa è una base sperimentale, non una riproduzione verificata del V5. Gli obiettivi sotto non sono ancora tutti implementati: vedi `README_MAC.md`.

## Specifiche e stile desiderati

- 1080×1920, 9:16, 30 fps, H.264/AAC.
- Niente musica incorporata; voce originale senza alterarne parole e velocità, stem VOICEOVER e SFX separati; audio misurato sul file finale, obiettivo circa −16 LUFS e true peak ≤ −1,5 dBTP.
- Testo leggibile in zona sicura; niente scritta fissa di branding o crediti facoltativi. Preservare eventuali attribuzioni obbligatorie delle licenze.
- Animazioni e SFX sincronizzati con cue condivisi, senza coprire la voce. Clip AI come supporto, senza presentarle come riprese autentiche dei luoghi.
- Struttura narrativa indicativa: hook, contesto, impatto, orientamento/viaggio, chiusura. Durata e ritmo seguono la voce: non sono obbligatori 30 secondi né una durata fissa per scena.

## Materiali per Reel

`reels/<nome>/` contiene il copione, `scenes.json`, `prompts.md`, la cartella delle clip e, dopo la preparazione, voce, caption, cue e mix in `prepared/`. La composizione `AutomaticReel` usa questi dati attraverso la pipeline documentata in `README_MAC.md`. I cambi scena e il typing sono semplificati rispetto al V5; la demo grafica `DemoSalento` rimane separata. Nessuna esportazione è necessaria per installare o verificare il progetto.
