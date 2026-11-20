/* Mostra AC – QR code e audio in diretta sulla rete locale.
   Usato da tv.html, desktop.html, ascolta.html, radio-ascolto.html e qr.html.
   Richiede qrcode.js (Kazuhiko Arase, licenza MIT). */
(function (w) {
  "use strict";

  const attendi = ms => new Promise(r => setTimeout(r, ms));

  /* ---------------- QR code ---------------- */
  function qrSvg(testo, colore = "#061a3a", sfondo = "#ffffff") {
    if (typeof qrcode !== "function") return "";
    qrcode.stringToBytes = qrcode.stringToBytesFuncs["UTF-8"];
    const q = qrcode(0, "L");
    q.addData(testo, "Byte");
    q.make();
    const n = q.getModuleCount(), m = 3, tot = n + m * 2;
    let d = "";
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${c + m} ${r + m}h1v1h-1z`;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${tot} ${tot}" shape-rendering="crispEdges" style="display:block;width:100%;height:auto">` +
      `<rect width="${tot}" height="${tot}" fill="${sfondo}"/><path d="${d}" fill="${colore}"/></svg>`;
  }
  function testoWifi(rete, password) {
    const e = s => String(s).replace(/([\\;,:"])/g, "\\$1");
    return password ? `WIFI:T:WPA;S:${e(rete)};P:${e(password)};;` : `WIFI:T:nopass;S:${e(rete)};;`;
  }

  /* ---------------- programma ponte ---------------- */
  const conServer = () => location.protocol === "http:" && !/github\.io$/.test(location.hostname);
  async function info() {
    const r = await fetch("/api/info", { cache: "no-store" });
    if (!r.ok) throw new Error("server");
    return r.json();
  }

  /* L'audio in diretta passa dalla stessa connessione delle pagine web (porta 8080):
     il PC manda al programma ponte piccoli pezzi di audio (PCM 16 bit mono, 24 kHz)
     e il programma li gira ai telefoni collegati. Niente firewall da aprire, niente UDP. */
  const FREQ = 24000;

  /* ---------------- trasmettitore (PC) ---------------- */
  class Trasmettitore {
    constructor(canale) {
      this.canale = canale; this.attivo = false; this.ascoltatori = 0;
      this.ctx = null; this.proc = null; this.pos = 0; this.coda = []; this.inCorso = false; this.ultimo = 0;
    }
    avvia(ctx, nodo) {
      if (this.attivo) return;
      this.attivo = true; this.ctx = ctx;
      const proc = ctx.createScriptProcessor(2048, 2, 1);
      const muto = ctx.createGain(); muto.gain.value = 0;
      nodo.connect(proc); proc.connect(muto); muto.connect(ctx.destination);
      this.proc = proc; this.nodo = nodo; this.muto = muto;
      const passo = ctx.sampleRate / FREQ;
      proc.onaudioprocess = e => {
        const ib = e.inputBuffer, l = ib.getChannelData(0), r = ib.numberOfChannels > 1 ? ib.getChannelData(1) : l;
        // ricampionamento lineare a 24 kHz, in mono
        const out = [];
        let p = this.pos;
        while (p < l.length - 1) {
          const i = Math.floor(p), f = p - i;
          const a = (l[i] + r[i]) / 2, b = (l[i + 1] + r[i + 1]) / 2;
          const v = Math.max(-1, Math.min(1, a + (b - a) * f));
          out.push(v < 0 ? v * 0x8000 : v * 0x7fff);
          p += passo;
        }
        this.pos = p - l.length;
        this.coda.push(Int16Array.from(out));
        this._invia();
      };
      // se nessuno ascolta per un po' comunque teniamo vivo il segnale "attivo"
      this._timer = setInterval(() => this._invia(true), 1000);
    }
    ferma() {
      this.attivo = false; this.coda = [];
      clearInterval(this._timer);
      try { this.nodo.disconnect(this.proc); } catch {}
      try { this.proc.disconnect(); this.muto.disconnect(); } catch {}
      this.proc = null;
    }
    async _invia(forza) {
      if (this.inCorso || !this.attivo) return;
      const tot = this.coda.reduce((n, a) => n + a.length, 0);
      if (tot < FREQ * 0.06 && !(forza && Date.now() - this.ultimo > 900)) return;   // pezzi da ~60 ms
      const buf = new Int16Array(tot); let o = 0;
      this.coda.forEach(a => { buf.set(a, o); o += a.length; }); this.coda = [];
      this.inCorso = true; this.ultimo = Date.now();
      try {
        const r = await fetch(`/api/flusso/invia?canale=${this.canale}`, { method: "POST", body: buf.buffer, headers: { "Content-Type": "application/octet-stream" } });
        const j = await r.json(); this.ascoltatori = j.ascoltatori || 0;
      } catch {}
      this.inCorso = false;
      if (this.coda.length > 20) this.coda = this.coda.slice(-4);   // rete lenta: non accumulare ritardo
    }
  }

  /* ---------------- ricevitore (telefono) ---------------- */
  function wavMuto() {
    // mezzo secondo di silenzio: suonato in loop sblocca l'audio su iPhone anche col tasto silenzioso
    const n = 4000, b = new ArrayBuffer(44 + n * 2), d = new DataView(b);
    const s = (o, t) => { for (let i = 0; i < t.length; i++) d.setUint8(o + i, t.charCodeAt(i)); };
    s(0, "RIFF"); d.setUint32(4, 36 + n * 2, true); s(8, "WAVE"); s(12, "fmt "); d.setUint32(16, 16, true); d.setUint16(20, 1, true);
    d.setUint16(22, 1, true); d.setUint32(24, 8000, true); d.setUint32(28, 16000, true); d.setUint16(32, 2, true); d.setUint16(34, 16, true);
    s(36, "data"); d.setUint32(40, n * 2, true);
    return URL.createObjectURL(new Blob([b], { type: "audio/wav" }));
  }
  class Ricevitore {
    constructor(canale, audio) {
      this.canale = canale; this.audio = audio; this.ctx = null; this.stato = "spento"; this.onStato = null;
      this._gen = 0; this.ctrl = null; this.testa = 0; this.ultimoDato = 0;
    }
    _imposta(s) { if (this.stato !== s) { this.stato = s; this.onStato && this.onStato(s); } }
    // va chiamato dentro il tocco dell'utente
    sblocca() {
      try { if (navigator.audioSession) navigator.audioSession.type = "playback"; } catch {}
      if (!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)({ latencyHint: "interactive" });
      this.ctx.resume().catch(() => {});
      try { this.guadagno || (this.guadagno = this.ctx.createGain(), this.guadagno.connect(this.ctx.destination)); } catch {}
      if (this.audio && !this.audio.src) { this.audio.src = wavMuto(); this.audio.loop = true; this.audio.volume = 0.01; }
      if (this.audio) this.audio.play().catch(() => {});
    }
    async connetti() {
      const gen = ++this._gen;
      this.chiudi();
      this._imposta("connessione");
      const ctrl = new AbortController(); this.ctrl = ctrl;
      let r;
      try { r = await fetch(`/api/flusso/ricevi?canale=${this.canale}&_=${Date.now()}`, { cache: "no-store", signal: ctrl.signal }); }
      catch { if (gen === this._gen) this._imposta("persa"); return; }
      if (!r.ok || !r.body) { if (gen === this._gen) this._imposta("persa"); return; }
      const lettore = r.body.getReader();
      let avanzo = null;
      this.testa = 0;
      try {
        while (gen === this._gen) {
          const { value, done } = await lettore.read();
          if (done) break;
          let dati = value;
          if (avanzo) { const t = new Uint8Array(avanzo.length + dati.length); t.set(avanzo); t.set(dati, avanzo.length); dati = t; avanzo = null; }
          if (dati.length % 2) { avanzo = dati.slice(dati.length - 1); dati = dati.slice(0, dati.length - 1); }
          if (dati.length) this._suona(dati);
        }
      } catch {}
      if (gen === this._gen) this._imposta("persa");
    }
    _suona(byte) {
      const ctx = this.ctx; if (!ctx) return;
      const pcm = new Int16Array(byte.buffer, byte.byteOffset, byte.length / 2);
      const buf = ctx.createBuffer(1, pcm.length, FREQ), ch = buf.getChannelData(0);
      for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;
      const ora = ctx.currentTime;
      if (this.testa < ora + 0.03) this.testa = ora + 0.12;          // partenza o buco: piccolo margine
      if (this.testa > ora + 0.6) return;                             // troppo ritardo accumulato: salto un pezzo
      const src = ctx.createBufferSource(); src.buffer = buf; src.connect(this.guadagno || ctx.destination);
      src.start(this.testa); this.testa += buf.duration;
      this.ultimoDato = Date.now();
      this._imposta("diretta");
    }
    chiudi() { if (this.ctrl) { try { this.ctrl.abort(); } catch {} this.ctrl = null; } }
  }

  w.MostraAC = { qrSvg, testoWifi, conServer, info, Trasmettitore, Ricevitore };
})(window);
