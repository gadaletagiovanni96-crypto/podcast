# Mostra AC – Studio Podcast, Radio, TV e PC anni 2000

# 🚀 INSTALLAZIONE DELLA MOSTRA (leggi prima questa parte)

Tutto si gestisce da una pagina sola, la **Regia**. Non serve Internet durante la mostra.

## Cosa serve
- Un **router** (anche quello di casa) a cui collegare i PC e i telefoni dei visitatori. Nelle sue impostazioni **disattiva l'isolamento dei client** (*AP isolation* / *rete ospiti*).
- Su ogni PC: **Google Chrome** o **Microsoft Edge**.

## 1 · A casa, con Internet (una volta sola per ogni PC)
1. Copia la cartella **Mostra AC** sul PC (per esempio sul Desktop).
2. Doppio clic su **`AVVIA.bat`** (sul Mac: `AVVIA-mac.command`).
   - La prima volta Windows chiede il permesso di amministratore: rispondi **Sì**.
   - Se manca Python lo installa da solo (serve Internet).
3. Si apre la **Regia**. Password: **`azione2026`**.
4. Scegli **che cosa fa questo PC**: 📺 TV · 🖥️ Desktop anni 2000 · 🎙️ Studio Podcast · 📻 Solo radio/regia. Dagli un nome (es. «PC TV»).
5. Attiva **Avvio automatico** se vuoi che la postazione parta da sola quando accendi il PC.
6. Scheda **🎬 Contenuti**: **trascina** dentro i video (TV o desktop) e gli audio della radio. Fatto.

## 2 · Alla mostra
- Accendi router e PC: ogni postazione parte da sola **a schermo intero** (oppure doppio clic su `AVVIA.bat`).
- I PC **si trovano da soli** sulla rete: li vedi nella scheda **📡 Tutti i PC**.
- Puoi aprire la Regia anche **dal telefono**: l'indirizzo è scritto nella finestra nera (es. `http://192.168.1.21:8080/regia`).

## 3 · QR code da stampare
Dalla Regia di **un solo PC** (il «principale», di solito quello della TV) apri **🔳 QR da stampare**:
1. scrivi nome e password del Wi-Fi;
2. premi **Scarica tutti i PNG** e stampali.

I QR puntano tutti al PC principale, che manda ogni visitatore al PC giusto. C'è anche il QR **Portale**: un solo QR da cui il visitatore sceglie radio, audio della TV o audio del PC.

> Nel router imposta un **IP fisso/riservato** (*DHCP reservation*) **solo per il PC principale**: così i QR stampati funzionano sempre.

## Durante la mostra
- **Uscire da una postazione**: tasto **X** → password → *Chiudi la postazione*.
- **Cambiare impostazioni o contenuti**: dalla Regia, anche a postazione accesa (le modifiche arrivano in pochi secondi; il video della TV si cambia appena è in pausa).
- **Audio in cuffia** di TV e desktop: interruttore nella scheda **Questo PC** della Regia, con la scelta se farlo uscire anche dalle casse.
- **Radio**: si accende/spegne dalla scheda **Contenuti**.

---

# 📚 Le postazioni nel dettaglio

## 🎙️ Studio Podcast

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
Password predefinita: **`azione2026`** → cambiala subito dal pannello animatore.

## 🔑 Come aprire il pannello animatore (vale per tutte e tre le postazioni)
Non c'è nessun lucchetto sullo schermo, così i ragazzi non lo toccano.
- Premi il tasto **X** sulla tastiera → si apre la richiesta della password.
- Senza tastiera (es. telefono con la Radio): **tieni premuto 3 secondi il logo giallo** in alto a sinistra.
- Se qualcuno esce dallo schermo intero con Esc, compare una schermata "Torna allo studio": anche lì l'animatore preme **X**.

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
2. Tieni premuto 3 secondi il **logo giallo** in alto a sinistra (o premi **X** se c'è una tastiera) → password (predefinita **`azione2026`**, separata da quella dello Studio Podcast).
3. Nel pannello: **"+ Carica audio dal dispositivo"** → scegli uno o più file (MP3 consigliato). Seleziona quello da far ascoltare e premi **"Salva e torna alla radio"**.
4. I ragazzi premono **PLAY / PAUSA** e **INIZIO** (riporta la traccia all'inizio). Quando l'audio finisce **torna all'inizio e resta in pausa**; se resta in pausa per 10 secondi torna da solo all'inizio.

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
2. Premi **X** sulla tastiera → password (predefinita **`azione2026`**, separata dalle altre postazioni).
3. **"+ Carica video dal PC"** → scegli il video (MP4 consigliato), selezionalo e premi **"Salva e torna alla TV"**.

## Comandi per i ragazzi
- **PLAY / PAUSA** (o clic in un punto qualsiasi dello schermo).
- **INIZIO**: ferma il video e torna alla schermata iniziale (quella blu con "PREMI ▶ PLAY").
- Tastiera / telecomando da presentazione: `Spazio`, `Invio`, `→`, `Pagina giù` = play/pausa · `←`, `Pagina su`, `Home`, `R` = inizio.
- A fine video **torna alla schermata iniziale in pausa**; se resta in pausa **10 secondi** torna da solo all'inizio (con conto alla rovescia a schermo).
- Mentre il video va, comandi e cursore spariscono dopo 3 secondi e ricompaiono muovendo il mouse.

## Impostazioni (pannello animatore)
- Scritta della schermata blu e numero del canale.
- Adattamento del video: intero con bande nere oppure riempi lo schermo.
- Effetto tubo catodico (righe, sfarfallio): **spento** se usi una TV vera, leggero/forte su un monitor moderno.
- Volume e cambio password.

## Consigli per la TV a tubo
- Imposta l'uscita del PC in 4:3 (es. 800×600 o 1024×768) e, se la TV lo permette, scegli "duplica schermo".
- I video lunghi occupano spazio nel browser: meglio file MP4 sotto 1–2 GB.

---

# 🖥️ PC AC (`desktop.html`)

Quarta postazione: simula il desktop di un computer anni 2000 (barra delle applicazioni, finestre, cartelle, fumetti di notifica), nei colori blu e giallo delle altre.

## Come si usa
1. Apri `desktop.html` con Chrome/Edge e clicca **"Accendi il PC"** (schermata di avvio e suono di benvenuto).
2. Premi **X** → password (predefinita **`azione2026`**) → pannello animatore.
3. **"+ Aggiungi video dal PC"**: scegli i video che compariranno nella cartella. Puoi **rinominarli**, **cambiare l'ordine** (▲) e **toglierli** (✕). Restano salvati nel browser.

## Cosa possono fare i ragazzi
- **Doppio clic** sulla cartella del desktop (o *menu → nome cartella*) per aprirla: dentro ci sono i video con anteprima e durata.
- **Doppio clic** su un video: si apre in una **finestra** (non a tutto schermo) con **Play/Pausa**, **Stop** e **barra di scorrimento** trascinabile. Clic sul video = play/pausa.
- Le finestre si possono **spostare** trascinando la barra blu del titolo, **ridurre a icona** (_) e **chiudere** (✕); dalla barra in basso si riaprono.
- Si possono aprire più video, ma ne suona **uno alla volta** (aprendone/avviandone un altro, il precedente va in pausa).
- A fine video si torna all'inizio in pausa.
- Su schermi touch basta un tocco al posto del doppio clic.

## Ritorno automatico al desktop
Se **nessun video è in riproduzione** e nessuno tocca mouse/tastiera per il tempo impostato (predefinito **60 secondi**, modificabile nel pannello), tutte le finestre si chiudono e ricompare il fumetto di benvenuto.

---

---

# 🌐 Dettagli tecnici

- `server.py` è il programma che gira su ogni PC (avviato da `AVVIA.bat`/`AVVIA-mac.command`): serve le pagine, i contenuti (cartella `contenuti/`), l'audio in diretta e il telecomando. Le impostazioni stanno in `impostazioni.json`.
- I PC si annunciano in broadcast sulla porta UDP 47800; le pagine usano la porta TCP 8080. Se il router blocca la ricerca automatica, nella scheda *Tutti i PC* si può aggiungere un PC a mano.
- Le postazioni vengono aperte in Chrome/Edge in modalità **chiosco** (schermo intero vero, senza barre), con un profilo separato nella cartella `.profilo-browser`.
- Indirizzi corti dei QR: `/` portale, `/r` radio, `/t` audio TV, `/d` audio desktop, `/telecomando`.
- Le pagine funzionano ancora anche aperte con doppio clic (senza programma), con il vecchio pannello animatore: in quel caso audio in cuffia, radio e telecomando non sono disponibili.
