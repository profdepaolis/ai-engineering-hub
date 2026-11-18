# VideoCodex e bozze KORA per Mac

Questo repository contiene i sorgenti e gli script preparati per VideoCodex su Mac, le verifiche dei componenti V5 originali e le successive bozze KORA. Le istruzioni operative sono nei rispettivi file `LEGGIMI.txt` e `videocodex-mac/README_MAC.md`.

## Risorse esterne

Per evitare di pubblicare media del cliente, font con diritti di distribuzione da verificare, archivi duplicati e file generati, questi non sono inclusi nel repository. Gli script che li richiedono non funzionano da un clone senza procurarsi separatamente le risorse autorizzate:

- `premium-v5-mac/GONDAR_FINAL/public/impact.ttf` e `arialbd.ttf`: font originali, necessari tra l'altro alla verifica e alla bozza V5.
- `kora-cinema/mare.mp4`, `musa.mp4` e `musica-next-to-you.mp3`; `kora-effetti/swipe-soft.mp3`.
- Foto, logo, voce, video artistico e altri materiali KORA: rimangono nell'ambiente di produzione dell'utente.

Usare i pacchetti e le risorse già predisposti su Drive o sul Mac e verificare i diritti d'uso e distribuzione prima di riutilizzarli. I sorgenti V5 originali sono conservati separatamente dalla precedente ricostruzione `videocodex-mac`.

## Stato delle verifiche

La verifica delle API V5 e quella audio sintetica sono state eseguite sul Mac. La bozza V5 KORA, che usa `TypingCamera` e `AnimatedUnderline` sopra un video artistico già renderizzato, è stata renderizzata sul Mac; l'audio della fonte è copiato senza ricodifica. La revisione visiva e sonora della bozza reale resta da completare; non si tratta di un'integrazione completa del motore audio o di tutti i componenti V5.
