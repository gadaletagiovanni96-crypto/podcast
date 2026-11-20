/* Mostra AC – QR code e audio in diretta sulla rete locale (WebRTC).
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
  async function invia(msg) {
    await fetch("/api/rtc/invia", { method: "POST", body: JSON.stringify(msg), headers: { "Content-Type": "application/json" } });
  }
  function attendiIce(pc, ms) {
    if (pc.iceGatheringState === "complete") return Promise.resolve();
    return new Promise(ok => {
      const fine = () => { pc.removeEventListener("icegatheringstatechange", contr); ok(); };
      const contr = () => { if (pc.iceGatheringState === "complete") fine(); };
      pc.addEventListener("icegatheringstatechange", contr);
      setTimeout(fine, ms);
    });
  }
  // Opus stereo e di buona qualità
  function opusStereo(sdp) {
    const m = sdp.match(/a=rtpmap:(\d+) opus\/48000/i);
    if (!m) return sdp;
    const pt = m[1], extra = "stereo=1;sprop-stereo=1;maxaveragebitrate=128000";
    const re = new RegExp(`a=fmtp:${pt} ([^\\r\\n]*)`);
    if (re.test(sdp)) return sdp.replace(re, (x, p) => `a=fmtp:${pt} ${p.replace(/;?(stereo|sprop-stereo|maxaveragebitrate)=\d+/g, "")};${extra}`);
    return sdp.replace(m[0], `${m[0]}\r\na=fmtp:${pt} ${extra}`);
  }

  /* ---------------- trasmettitore (PC) ---------------- */
  class Trasmettitore {
    constructor(canale) {
      this.canale = canale; this.peers = new Map(); this.stream = null;
      this.attivo = false; this.ips = []; this.onCambio = null;
    }
    get ascoltatori() { let n = 0; this.peers.forEach(p => { if (p.connectionState === "connected") n++; }); return n; }
    async avvia(stream) {
      this.stream = stream;
      if (this.attivo) return;
      this.attivo = true;
      try { const j = await info(); this.ips = j.tutti || [j.ip]; } catch { this.ips = []; }
      this._ciclo();
    }
    ferma() {
      this.attivo = false;
      [...this.peers.keys()].forEach(id => this._chiudi(id));
    }
    async _ciclo() {
      while (this.attivo) {
        try {
          const r = await fetch(`/api/rtc/ricevi?canale=${this.canale}&per=pc&n=${this.ascoltatori}`, { cache: "no-store" });
          const j = await r.json();
          for (const m of j.messaggi || []) await this._gestisci(m).catch(() => {});
        } catch {}
        await attendi(400);
      }
    }
    async _gestisci(m) {
      if (m.tipo === "ciao") return this._nuovo(String(m.da));
      const pc = this.peers.get(String(m.da));
      if (!pc) return;
      if (m.tipo === "risposta") await pc.setRemoteDescription({ type: "answer", sdp: m.sdp });
      else if (m.tipo === "arrivederci") this._chiudi(String(m.da));
    }
    _chiudi(id) {
      const pc = this.peers.get(id);
      if (pc) { try { pc.close(); } catch {} this.peers.delete(id); this.onCambio && this.onCambio(); }
    }
    // Chrome nasconde l'indirizzo del PC dietro un nome ".local": lo sostituiamo con l'indirizzo vero
    _indirizziVeri(sdp) {
      if (!this.ips.length) return sdp;
      return sdp.split("\r\n").flatMap(riga => {
        const m = riga.match(/^(a=candidate:\S+ \d+ \S+ \d+ )(\S+\.local)( \d+ typ host.*)$/i);
        return m ? this.ips.map(ip => m[1] + ip + m[3]) : [riga];
      }).join("\r\n");
    }
    async _nuovo(id) {
      if (!this.stream) return;
      this._chiudi(id);
      const pc = new RTCPeerConnection({ iceServers: [] });
      this.peers.set(id, pc);
      this.stream.getAudioTracks().forEach(t => pc.addTrack(t, this.stream));
      pc.onconnectionstatechange = () => {
        const s = pc.connectionState;
        if (s === "failed" || s === "closed") this._chiudi(id);
        if (s === "disconnected") setTimeout(() => { if (pc.connectionState === "disconnected") this._chiudi(id); }, 8000);
        this.onCambio && this.onCambio();
      };
      await pc.setLocalDescription(await pc.createOffer());
      await attendiIce(pc, 2000);
      await invia({ canale: this.canale, a: id, da: "pc", tipo: "offerta", sdp: this._indirizziVeri(pc.localDescription.sdp) });
      setTimeout(() => { if (pc.connectionState === "new") this._chiudi(id); }, 20000);
    }
  }

  /* ---------------- ricevitore (telefono) ---------------- */
  class Ricevitore {
    constructor(canale, audio) {
      this.canale = canale; this.audio = audio; this.pc = null; this.id = null;
      this.stato = "spento"; this.onStato = null; this._gen = 0;
    }
    _imposta(s) { this.stato = s; this.onStato && this.onStato(s); }
    async connetti() {
      const gen = ++this._gen;
      this.chiudi(false);
      this.id = Math.random().toString(36).slice(2, 12);
      this._imposta("connessione");
      const pc = new RTCPeerConnection({ iceServers: [] });
      this.pc = pc;
      pc.ontrack = e => {
        try { e.receiver.playoutDelayHint = 0; } catch {}
        try { e.receiver.jitterBufferTarget = 0; } catch {}
        this.audio.srcObject = e.streams[0] || new MediaStream([e.track]);
        this.audio.play().catch(() => this._imposta("tocca"));
      };
      pc.onconnectionstatechange = () => {
        if (gen !== this._gen) return;
        const s = pc.connectionState;
        if (s === "connected") this._imposta("diretta");
        else if (s === "failed" || s === "closed") this._imposta("persa");
        else if (s === "disconnected") setTimeout(() => { if (gen === this._gen && pc.connectionState === "disconnected") this._imposta("persa"); }, 4000);
      };
      await invia({ canale: this.canale, a: "pc", da: this.id, tipo: "ciao" });
      const limite = Date.now() + 10000;
      while (Date.now() < limite && gen === this._gen) {
        const r = await fetch(`/api/rtc/ricevi?canale=${this.canale}&per=${this.id}`, { cache: "no-store" });
        const j = await r.json();
        const off = (j.messaggi || []).find(m => m.tipo === "offerta");
        if (off) {
          await pc.setRemoteDescription({ type: "offer", sdp: off.sdp });
          const ans = await pc.createAnswer();
          await pc.setLocalDescription(ans);
          await attendiIce(pc, 1500);
          await invia({ canale: this.canale, a: "pc", da: this.id, tipo: "risposta", sdp: opusStereo(pc.localDescription.sdp) });
          return;
        }
        await attendi(300);
      }
      if (gen === this._gen) this._imposta("persa");
    }
    chiudi(avvisa = true) {
      if (this.pc) {
        if (avvisa && this.id) {
          try { navigator.sendBeacon("/api/rtc/invia", JSON.stringify({ canale: this.canale, a: "pc", da: this.id, tipo: "arrivederci" })); } catch {}
        }
        try { this.pc.close(); } catch {}
        this.pc = null;
      }
    }
  }

  w.MostraAC = { qrSvg, testoWifi, conServer, info, Trasmettitore, Ricevitore };
})(window);
