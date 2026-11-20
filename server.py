#!/usr/bin/env python3
"""Programma ponte della mostra (funziona senza Internet, sulla rete Wi-Fi locale).

Fa tre cose:
  1. telecomando della TV dal telefono;
  2. radio da ascoltare col telefono (gli audio vanno messi nella cartella "audio");
  3. audio in diretta di TV e desktop nelle cuffie dei visitatori (QR code).

Avvio:  Windows -> doppio clic su "avvia-telecomando-windows.bat"
        Mac     -> doppio clic su "avvia-telecomando-mac.command"
        altro   -> python3 server.py [porta] [pagina-da-aprire]
"""
import json, mimetypes, os, re, socket, sys, threading, time, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
PAGINA = sys.argv[2] if len(sys.argv) > 2 else "tv.html"
CARTELLA = os.path.dirname(os.path.realpath(__file__))
CARTELLA_AUDIO = os.path.join(CARTELLA, "audio")
ESTENSIONI_AUDIO = (".mp3", ".m4a", ".aac", ".wav", ".ogg", ".oga", ".opus", ".webm", ".flac")

mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("audio/aac", ".aac")
mimetypes.add_type("audio/ogg", ".ogg")
mimetypes.add_type("audio/ogg", ".opus")
mimetypes.add_type("audio/flac", ".flac")
mimetypes.add_type("application/javascript", ".js")

blocco = threading.Lock()
# telecomando + stato delle postazioni (per canale: "tv", "desktop")
comandi = {"id": 0, "azione": ""}
stati = {}            # canale -> (dati, istante)
# audio in diretta: il PC manda pezzi di audio, i telefoni li ricevono sulla stessa connessione web
flussi = {}           # canale -> {"pezzi": [(n, byte)], "n": ultimo numero, "visto": istante, "ascoltatori": n}
segnale = threading.Condition(blocco)


def flusso(canale):
    return flussi.setdefault(canale, {"pezzi": [], "n": 0, "visto": 0.0, "ascoltatori": 0})
FILE_CONFIG = os.path.join(CARTELLA, "impostazioni.json")


def leggi_config():
    try:
        with open(FILE_CONFIG, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError):
        c = {}
    return {"radio": bool(c.get("radio", True))}


def scrivi_config(c):
    try:
        with open(FILE_CONFIG, "w", encoding="utf-8") as f:
            json.dump(c, f)
    except OSError:
        pass


def indirizzi_locali():
    """Indirizzi IPv4 del PC: prima quello usato per uscire sulla rete, poi gli altri."""
    trovati = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        trovati.append(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            trovati.append(info[4][0])
    except OSError:
        pass
    puliti = []
    for ip in trovati:
        if ip.startswith("127.") or ip.startswith("169.254.") or ip in puliti:
            continue
        puliti.append(ip)
    return puliti or ["localhost"]


IPS = indirizzi_locali()
IP = IPS[0]


def nome_leggibile(file):
    base = os.path.splitext(file)[0]
    base = re.sub(r"^\d+[\s._-]+", "", base)          # "01 - titolo" -> "titolo"
    return re.sub(r"[_]+", " ", base).strip() or file


class Gestore(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "MostraAC"

    def log_message(self, *a):
        pass  # niente messaggi per ogni richiesta

    # ---------- utilità ----------
    def _invia(self, codice, corpo, tipo, extra=None):
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corpo)

    def _json(self, dati):
        self._invia(200, json.dumps(dati).encode(), "application/json; charset=utf-8")

    def _corpo_json(self):
        n = min(int(self.headers.get("Content-Length") or 0), 200000)
        try:
            return json.loads(self.rfile.read(n) or b"null")
        except ValueError:
            return None

    # ---------- GET ----------
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = u.path
        if p.startswith("/api/"):
            return self._api_get(p, q)
        return self._file(unquote(p))

    def _api_get(self, p, q):
        ora = time.time()
        canale = q.get("canale", "tv")
        with blocco:
            if p == "/api/info":
                return self._json({"ip": IP, "tutti": IPS, "porta": PORTA})
            if p == "/api/cmd":
                if q.get("azione") in ("play", "pausa", "toggle", "inizio"):
                    comandi["id"] += 1
                    comandi["azione"] = q["azione"]
                return self._json({"ok": True, "id": comandi["id"]})
            if p == "/api/poll":
                return self._json(dict(comandi))
            if p == "/api/stato":
                dati, t = stati.get(canale, (None, 0))
                return self._json({"eta": int(min(99999, ora - t)), "tv": dati})
            if p in ("/api/rtc/stato", "/api/flusso/stato"):
                f = flusso(canale)
                attivo = ora - f["visto"] < 4
                dati, t = stati.get(canale, (None, 0))
                return self._json({"attivo": attivo, "ascoltatori": f["ascoltatori"] if attivo else 0,
                                   "onda": dati if ora - t < 5 else None})
        if p == "/api/flusso/ricevi":
            return self._ricevi_flusso(canale)
        if p == "/api/config":
            return self._json(leggi_config())
        if p == "/api/radio":
            brani = []
            if not leggi_config()["radio"]:
                return self._json({"attiva": False, "brani": []})
            if os.path.isdir(CARTELLA_AUDIO):
                for f in sorted(os.listdir(CARTELLA_AUDIO), key=str.lower):
                    if f.lower().endswith(ESTENSIONI_AUDIO) and not f.startswith("."):
                        brani.append({"file": "audio/" + f, "nome": nome_leggibile(f),
                                      "mb": round(os.path.getsize(os.path.join(CARTELLA_AUDIO, f)) / 1048576, 1)})
            return self._json({"attiva": True, "brani": brani})
        self._invia(404, b"{}", "application/json")

    def _ricevi_flusso(self, canale):
        """Manda al telefono l'audio in diretta finché resta collegato."""
        self.close_connection = True
        try:
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frequenza", "24000")
        self.send_header("Connection", "close")
        self.end_headers()
        with blocco:
            f = flusso(canale)
            f["ascoltatori"] += 1
            ultimo = f["n"]
        try:
            while True:
                with blocco:
                    segnale.wait_for(lambda: flusso(canale)["n"] > ultimo, timeout=10)
                    f = flusso(canale)
                    nuovi = [b for (n, b) in f["pezzi"] if n > ultimo]
                    ultimo = f["n"]
                    if time.time() - f["visto"] > 30:
                        break                    # il PC ha smesso di trasmettere
                if nuovi:
                    self.wfile.write(b"".join(nuovi))
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            with blocco:
                flusso(canale)["ascoltatori"] -= 1

    # ---------- POST ----------
    def do_POST(self):
        p = urlparse(self.path).path
        q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        if p == "/api/flusso/invia":
            n = min(int(self.headers.get("Content-Length") or 0), 400000)
            pezzo = self.rfile.read(n)
            with blocco:
                f = flusso(q.get("canale", "tv"))
                f["visto"] = time.time()
                if pezzo:
                    f["n"] += 1
                    f["pezzi"].append((f["n"], pezzo))
                    del f["pezzi"][:-50]
                    segnale.notify_all()
                risposta = {"ascoltatori": f["ascoltatori"]}
            return self._json(risposta)
        dati = self._corpo_json()
        with blocco:
            if p == "/api/stato":
                if isinstance(dati, dict):
                    stati[q.get("canale", "tv")] = (dati, time.time())
                return self._json({"ok": True})
            if p == "/api/config" and isinstance(dati, dict):
                c = leggi_config()
                if "radio" in dati:
                    c["radio"] = bool(dati["radio"])
                scrivi_config(c)
                return self._json(c)
        self._invia(404, b"{}", "application/json")

    # ---------- file (con supporto Range, indispensabile per l'audio su iPhone) ----------
    def _file(self, percorso):
        # indirizzi corti per i QR code (QR più piccoli = più facili da inquadrare)
        corti = {"/t": "/ascolta.html?canale=tv", "/d": "/ascolta.html?canale=desktop", "/r": "/radio-ascolto.html"}
        if percorso in corti:
            return self._invia(302, b"", "text/plain", {"Location": corti[percorso]})
        if percorso in ("", "/"):
            percorso = "/index.html"
        completo = os.path.realpath(os.path.join(CARTELLA, percorso.lstrip("/")))
        if not completo.startswith(CARTELLA + os.sep) or not os.path.isfile(completo):
            return self._invia(404, "Non trovato".encode(), "text/plain; charset=utf-8")
        tipo = mimetypes.guess_type(completo)[0] or "application/octet-stream"
        if tipo.startswith("text/"):
            tipo += "; charset=utf-8"
        dim = os.path.getsize(completo)
        inizio, fine, codice = 0, dim - 1, 200
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip()) if rng else None
        if m and dim > 0:
            if m.group(1):
                inizio = int(m.group(1))
                if m.group(2):
                    fine = min(int(m.group(2)), dim - 1)
            elif m.group(2):
                inizio = max(0, dim - int(m.group(2)))
            if inizio > fine or inizio >= dim:
                return self._invia(416, b"", "text/plain", {"Content-Range": f"bytes */{dim}"})
            codice = 206
        lung = fine - inizio + 1 if dim else 0
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(lung))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        if codice == 206:
            self.send_header("Content-Range", f"bytes {inizio}-{fine}/{dim}")
        self.end_headers()
        if self.command == "HEAD" or lung == 0:
            return
        try:
            with open(completo, "rb") as f:
                f.seek(inizio)
                resta = lung
                while resta > 0:
                    pezzo = f.read(min(65536, resta))
                    if not pezzo:
                        break
                    self.wfile.write(pezzo)
                    resta -= len(pezzo)
        except (BrokenPipeError, ConnectionResetError):
            pass


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    os.makedirs(CARTELLA_AUDIO, exist_ok=True)
    try:
        srv = Server(("0.0.0.0", PORTA), Gestore)
    except OSError as e:
        print(f"\n  ERRORE: la porta {PORTA} è già in uso (il programma è già aperto?).\n  {e}\n")
        input("  Premi Invio per chiudere...")
        sys.exit(1)
    base = f"http://{IP}:{PORTA}"
    print("\n  ==================================================")
    print("   MOSTRA AC - PROGRAMMA PONTE ATTIVO")
    print("  ==================================================\n")
    print(f"   Indirizzo di questo PC:   {base}")
    if len(IPS) > 1:
        print("   (altri indirizzi: " + ", ".join(IPS[1:]) + ")")
    print()
    print(f"   TV ............ http://localhost:{PORTA}/tv.html")
    print(f"   Desktop ....... http://localhost:{PORTA}/desktop.html")
    print(f"   Telecomando ... {base}/telecomando.html")
    print(f"   Radio ......... {base}/radio-ascolto.html")
    print(f"   QR da stampare  http://localhost:{PORTA}/qr.html")
    print()
    print("   I telefoni devono essere collegati alla STESSA rete Wi-Fi del PC.")
    print("   NON chiudere questa finestra finché la mostra è aperta.\n")
    if PAGINA and PAGINA != "-":
        webbrowser.open(f"http://localhost:{PORTA}/{PAGINA}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
