# 🎙️ Studio Podcast – Azione Cattolica

Applicazione web (un solo file: `index.html`) per registrare mini podcast durante una mostra.
Non serve installare niente e funziona **anche senza internet**.

## Come avviarla
1. Copia `index.html` sul PC della mostra.
2. Aprilo con **Google Chrome** o **Microsoft Edge** (doppio clic, oppure trascinalo nel browser).
3. Premi **"Accendi lo studio"** → si apre lo schermo intero e il browser chiede il permesso per il microfono: premi **Consenti**.

### Impostazioni consigliate per il browser (da fare una volta)
- **Chrome → Impostazioni → Download**: disattiva *"Chiedi dove salvare ogni file"*, così i podcast finiscono direttamente nella cartella **Download** senza finestre.
- Se il browser chiede *"Consentire download multipli?"* rispondi **Consenti**.

## Password animatore
Password predefinita: **`azione2026`** → cambiala subito dal pannello animatore (lucchetto in alto a destra).

## Come funziona per i ragazzi
1. Premono il grande pulsante giallo **REGISTRA** → conto alla rovescia 3‑2‑1 con bip.
2. Durante la registrazione: **Pausa / Riprendi** e **Ho finito**.
3. Riascoltano il podcast; se non piace possono **Rifarlo da capo**.
4. Scrivono **i nomi dei componenti** (obbligatorio, almeno uno) e un titolo facoltativo.
5. **Salva** → il file va in *Download* con un nome tipo
   `Podcast_2026-11-20_15-30-12_La-nostra-estate_Mario_Anna.wav`.
6. Schermata di festa e, dopo 10 secondi, lo studio torna pronto per il gruppo successivo.

## Funzioni aggiuntive
- **Schermo intero protetto**: se qualcuno preme Esc compare una schermata che chiede di tornare allo studio; solo con la password si esce davvero.
- **Indicatore del microfono** per provare la voce prima di iniziare e **onde animate** durante la registrazione.
- **Durata massima** (predefinita 5 minuti) con avviso negli ultimi 30 secondi e stop automatico.
- **File WAV** con volume normalizzato automaticamente (si apre su qualsiasi PC/telefono). In alternativa formato compresso più leggero.
- **Riduzione del rumore di fondo** (utile in mostra, disattivabile).
- **Scelta del microfono** se ne colleghi uno esterno (consigliato!).
- **Registro dei podcast** salvati con esportazione in CSV (Excel) e contatore "podcast registrati oggi".
- Schermo che non va in standby, tasto destro e ricarica pagina bloccati, avviso se il microfono si scollega.
- Titolo e sottotitolo in alto personalizzabili.

## Modalità "chiosco" (ancora più sicura, facoltativa)
Per impedire del tutto l'uscita dall'app, avvia Chrome così (Windows, da un collegamento):
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk "C:\percorso\index.html"
```
Per chiudere in modalità chiosco: `Alt+F4`.

## Consigli pratici
- Usa un **microfono USB** o delle cuffie con microfono: la qualità migliora tantissimo.
- Fai una registrazione di prova prima dell'apertura della mostra.
- A fine giornata scarica il registro CSV dal pannello animatore.

---

# 📻 Radio AC (`radio.html`)

Seconda postazione: una "radio" che fa ascoltare un audio scelto dall'animatore. Ottimizzata per **smartphone e tablet** (verticale e orizzontale), funziona anche su PC.

## Come si usa
1. Apri `radio.html` e tocca **"Accendi la radio"** (si mette a schermo intero).
2. Tocca il **lucchetto** in alto a destra → password (predefinita **`azione2026`**, separata da quella dello Studio Podcast).
3. Nel pannello: **"+ Carica audio dal dispositivo"** → scegli uno o più file (MP3 consigliato). Seleziona quello da far ascoltare e premi **"Salva e torna alla radio"**.
4. I ragazzi premono **PLAY / PAUSA** e **INIZIO** (riporta la traccia all'inizio). Quando l'audio finisce **riparte automaticamente da capo**; se resta in pausa per 10 secondi torna da solo all'inizio.

I file caricati restano salvati nel browser di quel dispositivo: anche chiudendo la pagina non serve ricaricarli.

## Note per i telefoni
- **Android (Chrome)**: schermo intero e blocco funzionano.
- **iPhone (Safari)**: Apple non permette lo schermo intero alle pagine web; usa *Condividi → Aggiungi alla schermata Home* e attiva *Impostazioni → Accessibilità → Accesso guidato* per bloccare il telefono sull'app. Il volume si regola con i tasti del telefono.
- Per aprire la pagina su un telefono la cosa più semplice è pubblicarla online (es. GitHub Pages) e aprire il link.

---

# 📺 TV AC (`tv.html`)

Terza postazione: trasmette un video scelto dall'animatore, con lo stile di un vecchio televisore / videoregistratore (schermata blu, scritte verdi "▶ PLAY", "❚❚ PAUSA", effetto neve). Pensata per essere proiettata su una **TV a tubo catodico** (formato 4:3, scritte grandi e tenute lontane dai bordi).

## Come si usa
1. Apri `tv.html` con Chrome/Edge sul PC collegato alla TV e clicca (o premi un tasto) per accenderla.
2. Lucchetto in alto a destra → password (predefinita **`azione2026`**, separata dalle altre postazioni).
3. **"+ Carica video dal PC"** → scegli il video (MP4 consigliato), selezionalo e premi **"Salva e torna alla TV"**.

## Comandi per i ragazzi
- **PLAY / PAUSA** (o clic in un punto qualsiasi dello schermo).
- **INIZIO**: ferma il video e torna alla schermata iniziale (quella blu con "PREMI ▶ PLAY").
- Tastiera / telecomando da presentazione: `Spazio`, `Invio`, `→`, `Pagina giù` = play/pausa · `←`, `Pagina su`, `Home`, `R` = inizio.
- A fine video **riparte da capo**; se resta in pausa **10 secondi** torna da solo all'inizio (con conto alla rovescia a schermo).
- Mentre il video va, comandi e cursore spariscono dopo 3 secondi e ricompaiono muovendo il mouse.

## Impostazioni (pannello animatore)
- Scritta della schermata blu e numero del canale.
- Adattamento del video: intero con bande nere oppure riempi lo schermo.
- Effetto tubo catodico (righe, sfarfallio): **spento** se usi una TV vera, leggero/forte su un monitor moderno.
- Volume e cambio password.

## Consigli per la TV a tubo
- Imposta l'uscita del PC in 4:3 (es. 800×600 o 1024×768) e, se la TV lo permette, scegli "duplica schermo".
- I video lunghi occupano spazio nel browser: meglio file MP4 sotto 1–2 GB.
