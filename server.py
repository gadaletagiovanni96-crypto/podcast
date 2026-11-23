#!/usr/bin/env python3
"""Mostra AC - programma ponte (funziona senza Internet, sulla rete locale della mostra).

Si avvia con AVVIA.bat (Windows) o AVVIA-mac.command (Mac): è lo stesso su tutti i PC.
La prima volta si apre la Regia e si sceglie cosa fa questo PC (TV, desktop, studio, radio).
Dalle volte successive la postazione parte da sola a schermo intero.

Opzioni (per prove):  python3 server.py [--porta 8080] [--senza-browser]
"""
import json, mimetypes, os, re, shutil, socket, subprocess, sys, threading, time, uuid, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote
from urllib.request import build_opener, ProxyHandler, Request
from concurrent.futures import ThreadPoolExecutor

ARGOMENTI = sys.argv[1:]
PORTA = int(ARGOMENTI[ARGOMENTI.index("--porta") + 1]) if "--porta" in ARGOMENTI else 8080
SENZA_BROWSER = "--senza-browser" in ARGOMENTI
SENZA_BROADCAST = "--senza-broadcast" in ARGOMENTI   # solo per le prove
# le richieste agli altri PC della mostra non devono mai passare da un proxy di Windows
DIRETTO = build_opener(ProxyHandler({}))
PORTA_SCOPERTA = 47800           # UDP: i PC della mostra si trovano da soli
CARTELLA = os.path.dirname(os.path.realpath(__file__))
CARTELLA_CONTENUTI = os.path.join(CARTELLA, "contenuti")
TIPI_MEDIA = {
    "tv": (".mp4", ".m4v", ".webm", ".mov", ".ogv", ".mkv"),
    "desktop": (".mp4", ".m4v", ".webm", ".mov", ".ogv", ".mkv"),
    "radio": (".mp3", ".m4a", ".aac", ".wav", ".ogg", ".oga", ".opus", ".webm", ".flac"),
}
PAGINE_RUOLO = {"tv": "tv.html", "desktop": "desktop.html", "studio": "index.html"}
NOMI_RUOLO = {"tv": "TV a tubo catodico", "desktop": "Desktop anni 2000", "studio": "Studio Podcast", "radio": "Solo radio / regia"}

for est, tipo in ((".m4a", "audio/mp4"), (".aac", "audio/aac"), (".ogg", "audio/ogg"), (".opus", "audio/ogg"),
                  (".flac", "audio/flac"), (".js", "application/javascript"), (".mkv", "video/x-matroska"),
                  (".m4v", "video/mp4"), (".mov", "video/quicktime")):
    mimetypes.add_type(tipo, est)

blocco = threading.Lock()
segnale = threading.Condition(blocco)
comandi = {"id": 0, "azione": ""}       # telecomando della TV
stati = {}                              # canale -> (dati, istante): cosa sta andando
flussi = {}                             # canale -> audio in diretta
compagni = {}                           # id -> info degli altri PC della mostra
browser = {"processo": None}


def flusso(canale):
    return flussi.setdefault(canale, {"pezzi": [], "n": 0, "visto": 0.0, "ascoltatori": 0})


# ------------------------------------------------------------------ impostazioni
FILE_CONFIG = os.path.join(CARTELLA, "impostazioni.json")
PREDEFINITE = {
    "id": "", "nome": "", "ruolo": None, "password": "azione2026", "radio": True,
    "avvio_automatico": False, "wifi": {"rete": "", "pwd": ""}, "manuali": [],
    "tv": {"titolo": "TV AC", "canale": "CH 03", "adatta": "contain", "crt": "off", "volume": 100,
           "ascolto": False, "casse": True, "attivo": ""},
    "desktop": {"cartella": "I nostri video", "sfondo": "PC AC", "inattivita": 60, "volume": 100,
                "ascolto": False, "casse": True},
}


def _unisci(base, nuovo):
    out = dict(base)
    for k, v in (nuovo or {}).items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            out[k] = _unisci(base[k], v)
        elif k in base:
            out[k] = v
    return out


def leggi_config():
    try:
        with open(FILE_CONFIG, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError):
        c = {}
    c = _unisci(PREDEFINITE, c)
    if not c["id"]:
        c["id"] = uuid.uuid4().hex[:10]
        scrivi_config(c)
    if not c["nome"]:
        c["nome"] = socket.gethostname().split(".")[0][:30] or "PC"
    return c


def scrivi_config(c):
    try:
        tmp = FILE_CONFIG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
        os.replace(tmp, FILE_CONFIG)
    except OSError:
        pass


CONFIG = leggi_config()


def config_pubblica(c=None):
    c = dict(c or CONFIG)
    c.pop("password", None)
    return c


# ------------------------------------------------------------------ rete
def indirizzi_locali():
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
        if not (ip.startswith("127.") or ip.startswith("169.254.") or ip in puliti):
            puliti.append(ip)
    return puliti or ["127.0.0.1"]


IPS = indirizzi_locali()
IP = IPS[0]


# ------------------------------------------------------------------ contenuti
def cartella_media(tipo):
    d = os.path.join(CARTELLA_CONTENUTI, tipo)
    os.makedirs(d, exist_ok=True)
    return d


def nome_leggibile(file):
    base = os.path.splitext(file)[0]
    base = re.sub(r"^\d+[\s._-]+", "", base)          # "01 - titolo" -> "titolo"
    return re.sub(r"[_]+", " ", base).strip() or file


def elenco_media(tipo):
    d = cartella_media(tipo)
    out = []
    for f in sorted(os.listdir(d), key=str.lower):
        p = os.path.join(d, f)
        if f.startswith(".") or not os.path.isfile(p) or not f.lower().endswith(TIPI_MEDIA[tipo]):
            continue
        st = os.stat(p)
        out.append({"file": f, "nome": nome_leggibile(f), "url": f"contenuti/{tipo}/" + quote(f),
                    "mb": round(st.st_size / 1048576, 1), "firma": f"{st.st_size}-{int(st.st_mtime)}"})
    return out


def nome_sicuro(nome, tipo):
    nome = os.path.basename(nome.replace("\\", "/")).strip()
    nome = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", nome)[:120]
    if not nome or nome.startswith(".") or not nome.lower().endswith(TIPI_MEDIA[tipo]):
        return None
    return nome


def migra_vecchia_cartella_audio():
    vecchia = os.path.join(CARTELLA, "audio")
    if not os.path.isdir(vecchia):
        return
    nuova = cartella_media("radio")
    for f in os.listdir(vecchia):
        if f.lower().endswith(TIPI_MEDIA["radio"]) and not os.path.exists(os.path.join(nuova, f)):
            try:
                shutil.move(os.path.join(vecchia, f), os.path.join(nuova, f))
            except OSError:
                pass


# ------------------------------------------------------------------ chi sono / gli altri PC
def identita():
    c = CONFIG
    brani = len(elenco_media("radio")) if c["radio"] else 0
    ascolto = bool(c["ruolo"] in ("tv", "desktop") and c[c["ruolo"]]["ascolto"])
    f = flusso(c["ruolo"] or "-")
    return {"app": "MostraAC", "id": c["id"], "nome": c["nome"], "ruolo": c["ruolo"], "ip": IP, "porta": PORTA,
            "ascolto": ascolto, "trasmette": time.time() - f["visto"] < 4, "ascoltatori": f["ascoltatori"],
            "radio": brani}


def ciclo_scoperta():
    """Ogni 3 secondi annuncia questo PC in broadcast e ascolta gli annunci degli altri."""
    ric = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ric.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            ric.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    try:
        ric.bind(("", PORTA_SCOPERTA))
    except OSError:
        ric = None
    inv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inv.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def ascolta():
        while ric:
            try:
                dati, da = ric.recvfrom(4096)
                info = json.loads(dati.decode("utf-8"))
                if info.get("app") == "MostraAC" and info.get("id") != CONFIG["id"]:
                    info["ip"] = da[0]
                    info["visto"] = time.time()
                    with blocco:
                        compagni[info["id"]] = info
            except (OSError, ValueError):
                time.sleep(0.5)
    threading.Thread(target=ascolta, daemon=True).start()

    while not SENZA_BROADCAST:
        msg = json.dumps(identita()).encode("utf-8")
        destinazioni = {"255.255.255.255"}
        for ip in IPS:
            parti = ip.split(".")
            if len(parti) == 4:
                destinazioni.add(".".join(parti[:3] + ["255"]))
        for d in destinazioni:
            try:
                inv.sendto(msg, (d, PORTA_SCOPERTA))
            except OSError:
                pass
        time.sleep(3)


def chiedi_identita(indirizzo, attesa=2):
    """Chiede a un indirizzo "ip:porta" se è un PC della mostra; se sì lo aggiunge all'elenco."""
    try:
        # ci presentiamo: così anche l'altro PC trova subito noi
        richiesta = Request(f"http://{indirizzo}/api/identita", headers={"X-MostraAC": f"{IP}:{PORTA}"})
        with DIRETTO.open(richiesta, timeout=attesa) as r:
            info = json.loads(r.read(4096).decode("utf-8"))
    except (OSError, ValueError):
        return False
    if info.get("app") != "MostraAC" or info.get("id") == CONFIG["id"]:
        return False
    info["visto"] = time.time()
    with blocco:
        compagni[info["id"]] = info
    return True


def ciclo_manuali():
    """PC aggiunti a mano dalla Regia + PC già trovati: li ricontrolla ogni 5 secondi."""
    while True:
        conosciuti = {f"{v['ip']}:{v['porta']}" for v in list(compagni.values())}
        for ind in set(CONFIG.get("manuali", [])) | conosciuti:
            chiedi_identita(ind)
        time.sleep(5)


ricerca = {"in_corso": False, "ultima": 0.0}


def cerca_pc():
    """Ricerca sicura anche se il router blocca il broadcast: prova uno per uno gli indirizzi
    della rete locale sulla porta del programma (la stessa che usano i telefoni)."""
    if ricerca["in_corso"]:
        return
    ricerca["in_corso"] = True
    try:
        porte = sorted({PORTA, 8080})
        candidati = []
        for ip in IPS:
            parti = ip.split(".")
            if len(parti) != 4 or ip.startswith("127."):
                continue
            for n in range(1, 255):
                c = ".".join(parti[:3] + [str(n)])
                for porta in porte:
                    if not (c in IPS and porta == PORTA):
                        candidati.append(f"{c}:{porta}")
        with ThreadPoolExecutor(max_workers=64) as ex:
            list(ex.map(lambda ind: chiedi_identita(ind, 0.8), candidati))
    finally:
        ricerca["in_corso"] = False
        ricerca["ultima"] = time.time()


def ciclo_ricerca():
    time.sleep(2)
    while True:
        cerca_pc()
        time.sleep(60)


def rete():
    ora = time.time()
    with blocco:
        altri = [dict(v, online=ora - v["visto"] < 12) for v in compagni.values() if ora - v["visto"] < 600]
    io = dict(identita(), online=True, questo=True)
    return [io] + sorted(altri, key=lambda x: (x.get("ruolo") or "z", x.get("nome", "")))


def trova(ruolo=None, radio=False):
    for pc in rete():
        if not pc["online"]:
            continue
        if radio and pc.get("radio"):
            return pc
        if ruolo and pc.get("ruolo") == ruolo:
            return pc
    return None


# ------------------------------------------------------------------ browser e avvio automatico
def trova_browser():
    candidati = []
    if sys.platform.startswith("win"):
        for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(var)
            if base:
                candidati += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                              os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    elif sys.platform == "darwin":
        candidati = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                     "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    else:
        candidati = [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge")]
    for c in candidati:
        if c and os.path.isfile(c):
            return c
    return None


def avvia_postazione():
    ruolo = CONFIG["ruolo"]
    if ruolo not in PAGINE_RUOLO:
        return False
    chiudi_postazione()
    url = f"http://localhost:{PORTA}/{PAGINE_RUOLO[ruolo]}?kiosk=1"
    exe = trova_browser()
    if not exe:
        webbrowser.open(url)
        return True
    profilo = os.path.join(CARTELLA, ".profilo-browser")
    args = [exe, "--kiosk", url, f"--user-data-dir={profilo}", "--no-first-run", "--no-default-browser-check",
            "--autoplay-policy=no-user-gesture-required", "--disable-session-crashed-bubble",
            "--disable-features=Translate,TranslateUI", "--overscroll-history-navigation=0",
            "--disable-pinch", "--noerrdialogs", "--use-fake-ui-for-media-stream"]
    try:
        browser["processo"] = subprocess.Popen(args)
    except OSError:
        webbrowser.open(url)
    return True


def chiudi_postazione():
    """Chiude il browser della postazione. Chrome/Edge su Windows passano spesso la finestra a un
    altro processo (e dopo un riavvio del programma non sappiamo quale sia): per questo chiudiamo
    tutti i processi avviati con il profilo della mostra, riconoscibili dalla loro riga di comando."""
    p = browser.get("processo")
    if p and p.poll() is None:
        try:
            p.terminate()
            p.wait(3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    browser["processo"] = None
    profilo = os.path.join(CARTELLA, ".profilo-browser")
    try:
        if sys.platform.startswith("win"):
            cerca = profilo.replace("'", "''")
            comando = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('"
                       + cerca + "') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
                           timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            subprocess.run(["pkill", "-f", "--", "user-data-dir=" + profilo], timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def imposta_avvio_automatico(attivo):
    """Windows: un collegamento nella cartella Esecuzione automatica. Mac: un LaunchAgent."""
    try:
        if sys.platform.startswith("win"):
            cartella = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            file = os.path.join(cartella, "Mostra AC.bat")
            if attivo:
                with open(file, "w", newline="\r\n") as f:
                    f.write(f'@echo off\ncd /d "{CARTELLA}"\nstart "Mostra AC" /min cmd /c "AVVIA.bat"\n')
            elif os.path.exists(file):
                os.remove(file)
            return True
        if sys.platform == "darwin":
            file = os.path.expanduser("~/Library/LaunchAgents/it.mostraac.avvio.plist")
            if attivo:
                os.makedirs(os.path.dirname(file), exist_ok=True)
                with open(file, "w") as f:
                    f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>Label</key><string>it.mostraac.avvio</string>
<key>ProgramArguments</key><array><string>/usr/bin/python3</string><string>{os.path.join(CARTELLA, "server.py")}</string></array>
<key>RunAtLoad</key><true/></dict></plist>''')
            elif os.path.exists(file):
                os.remove(file)
            return True
    except OSError:
        pass
    return False


def apri_cartella(tipo):
    d = cartella_media(tipo)
    try:
        if sys.platform.startswith("win"):
            os.startfile(d)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", d])
        else:
            subprocess.Popen(["xdg-open", d])
        return True
    except OSError:
        return False


# ------------------------------------------------------------------ server web
class Gestore(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "MostraAC"

    def log_message(self, *a):
        pass

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

    def _json(self, dati, codice=200):
        self._invia(codice, json.dumps(dati, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _corpo_json(self):
        n = min(int(self.headers.get("Content-Length") or 0), 200000)
        try:
            return json.loads(self.rfile.read(n) or b"null")
        except ValueError:
            return None

    def _autorizzato(self):
        return unquote(self.headers.get("X-Password", "")) == CONFIG["password"]

    def _vai(self, url):
        self._invia(302, b"", "text/plain", {"Location": url})

    # ---------------- GET ----------------
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = u.path
        if p.startswith("/api/"):
            return self._api_get(p, q)
        # indirizzi corti dei QR: portano al PC giusto, ovunque sia nella rete
        corti = {"/t": ("tv", "/ascolta.html?canale=tv"), "/d": ("desktop", "/ascolta.html?canale=desktop"),
                 "/telecomando": ("tv", "/telecomando.html"), "/r": (None, "/radio-ascolto.html")}
        if p in corti:
            ruolo, pagina = corti[p]
            pc = trova(radio=True) if ruolo is None else trova(ruolo)
            if pc:
                host = "" if pc.get("questo") else f"http://{pc['ip']}:{pc['porta']}"
                return self._vai(host + pagina)
            return self._vai("/portale.html?manca=" + (ruolo or "radio"))
        if p in ("", "/"):
            return self._vai("/portale.html")
        if p == "/regia":
            return self._vai("/regia.html")
        return self._file(unquote(p))

    def _api_get(self, p, q):
        ora = time.time()
        canale = q.get("canale", "tv")
        if p == "/api/info":
            return self._json({"ip": IP, "tutti": IPS, "porta": PORTA})
        if p == "/api/identita":
            chi = self.headers.get("X-MostraAC", "")
            if re.match(r"^[\d.]+:\d+$", chi) and chi != f"{IP}:{PORTA}":
                threading.Thread(target=chiedi_identita, args=(chi,), daemon=True).start()
            return self._json(identita())
        if p == "/api/rete":
            return self._json({"pc": rete(), "ricerca": ricerca["in_corso"]})
        if p == "/api/rete/cerca":
            threading.Thread(target=cerca_pc, daemon=True).start()
            return self._json({"ok": True})
        if p == "/api/config":
            return self._json(config_pubblica())
        if p == "/api/postazione":
            ruolo = CONFIG["ruolo"]
            return self._json({"ruolo": ruolo, "nome": CONFIG["nome"],
                               "impostazioni": CONFIG.get(ruolo) if ruolo in ("tv", "desktop") else {},
                               "media": elenco_media(ruolo) if ruolo in ("tv", "desktop") else []})
        if p.startswith("/api/media/"):
            tipo = p.split("/")[3]
            if tipo in TIPI_MEDIA:
                return self._json({"file": elenco_media(tipo)})
        if p == "/api/radio":
            if not CONFIG["radio"]:
                return self._json({"attiva": False, "brani": []})
            return self._json({"attiva": True, "brani": elenco_media("radio")})
        if p == "/api/flusso/ricevi":
            return self._ricevi_flusso(canale)
        with blocco:
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
        self._json({"errore": "sconosciuto"}, 404)

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
                        break
                if nuovi:
                    self.wfile.write(b"".join(nuovi))
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            with blocco:
                flusso(canale)["ascoltatori"] -= 1

    # ---------------- POST ----------------
    def do_POST(self):
        global CONFIG
        u = urlparse(self.path)
        p = u.path
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
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

        # caricamento di un file (può essere grande: lo scriviamo a pezzi)
        m = re.match(r"^/api/media/(\w+)/carica$", p)
        if m:
            tipo = m.group(1)
            if not self._autorizzato():
                return self._json({"errore": "password"}, 403)
            nome = nome_sicuro(q.get("nome", ""), tipo) if tipo in TIPI_MEDIA else None
            if not nome:
                return self._json({"errore": "Tipo di file non adatto"}, 400)
            resta = int(self.headers.get("Content-Length") or 0)
            dest = os.path.join(cartella_media(tipo), nome)
            tmp = dest + ".caricamento"
            try:
                with open(tmp, "wb") as f:
                    while resta > 0:
                        pezzo = self.rfile.read(min(1048576, resta))
                        if not pezzo:
                            break
                        f.write(pezzo)
                        resta -= len(pezzo)
                if resta > 0:
                    raise OSError("caricamento interrotto")
                os.replace(tmp, dest)
            except OSError as e:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                return self._json({"errore": str(e)}, 500)
            return self._json({"ok": True, "file": nome})

        dati = self._corpo_json()
        if p == "/api/stato":
            with blocco:
                if isinstance(dati, dict):
                    stati[q.get("canale", "tv")] = (dati, time.time())
            return self._json({"ok": True})
        if p == "/api/verifica-password":
            ok = isinstance(dati, dict) and dati.get("password") == CONFIG["password"]
            return self._json({"ok": ok})

        # tutto il resto richiede la password della Regia
        if not self._autorizzato():
            return self._json({"errore": "password"}, 403)
        if p == "/api/config" and isinstance(dati, dict):
            vecchio_auto = CONFIG["avvio_automatico"]
            nuovo = _unisci(CONFIG, {k: v for k, v in dati.items() if k not in ("id",)})
            if nuovo["ruolo"] not in (None, "tv", "desktop", "studio", "radio"):
                nuovo["ruolo"] = None
            if not str(nuovo["password"]).strip():
                nuovo["password"] = CONFIG["password"]
            nuovo["manuali"] = [str(x).strip() for x in nuovo.get("manuali", []) if str(x).strip()][:20]
            CONFIG = nuovo
            scrivi_config(CONFIG)
            if CONFIG["avvio_automatico"] != vecchio_auto:
                imposta_avvio_automatico(CONFIG["avvio_automatico"])
            return self._json(config_pubblica())
        m = re.match(r"^/api/media/(\w+)/(elimina|rinomina|apri)$", p)
        if m and m.group(1) in TIPI_MEDIA:
            tipo, azione = m.groups()
            if azione == "apri":
                return self._json({"ok": apri_cartella(tipo)})
            vecchio = nome_sicuro((dati or {}).get("file", ""), tipo)
            if not vecchio or not os.path.isfile(os.path.join(cartella_media(tipo), vecchio)):
                return self._json({"errore": "File non trovato"}, 404)
            try:
                if azione == "elimina":
                    os.remove(os.path.join(cartella_media(tipo), vecchio))
                else:
                    nuovo = (dati or {}).get("nuovo", "")
                    est = os.path.splitext(vecchio)[1]
                    if not nuovo.lower().endswith(est.lower()):
                        nuovo += est
                    nuovo = nome_sicuro(nuovo, tipo)
                    if not nuovo:
                        return self._json({"errore": "Nome non valido"}, 400)
                    os.replace(os.path.join(cartella_media(tipo), vecchio), os.path.join(cartella_media(tipo), nuovo))
            except OSError as e:
                return self._json({"errore": str(e)}, 500)
            return self._json({"ok": True})
        if p == "/api/postazione/avvia":
            return self._json({"ok": avvia_postazione()})
        if p == "/api/postazione/chiudi":
            threading.Thread(target=lambda: (time.sleep(0.5), chiudi_postazione()), daemon=True).start()
            return self._json({"ok": True})
        self._json({"errore": "sconosciuto"}, 404)

    # ---------------- file (con supporto Range, indispensabile per audio e video) ----------------
    def _file(self, percorso):
        completo = os.path.realpath(os.path.join(CARTELLA, percorso.lstrip("/")))
        nascosto = any(parte.startswith(".") for parte in os.path.relpath(completo, CARTELLA).split(os.sep))
        if (not completo.startswith(CARTELLA + os.sep) or nascosto or not os.path.isfile(completo)
                or completo.endswith((".py", ".json", ".bat", ".command", ".caricamento"))):
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
                    pezzo = f.read(min(262144, resta))
                    if not pezzo:
                        break
                    self.wfile.write(pezzo)
                    resta -= len(pezzo)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # browser chiuso o telefono che si stacca: la connessione si interrompe, è normale
        errore = sys.exc_info()[1]
        if isinstance(errore, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, TimeoutError)):
            return
        super().handle_error(request, client_address)


if __name__ == "__main__":
    for t in TIPI_MEDIA:
        cartella_media(t)
    migra_vecchia_cartella_audio()
    try:
        srv = Server(("0.0.0.0", PORTA), Gestore)
    except OSError as e:
        print(f"\n  Il programma è già aperto (porta {PORTA} occupata).\n  {e}\n")
        if not SENZA_BROWSER:
            webbrowser.open(f"http://localhost:{PORTA}/regia.html")
        time.sleep(4)
        sys.exit(0)
    threading.Thread(target=ciclo_scoperta, daemon=True).start()
    threading.Thread(target=ciclo_manuali, daemon=True).start()
    threading.Thread(target=ciclo_ricerca, daemon=True).start()
    base = f"http://{IP}:{PORTA}"
    print("\n  ==================================================")
    print("   MOSTRA AC - PROGRAMMA ATTIVO")
    print("  ==================================================\n")
    print(f"   Questo PC:  {CONFIG['nome']}   ({NOMI_RUOLO.get(CONFIG['ruolo'], 'postazione non ancora scelta')})")
    print(f"   Indirizzo:  {base}\n")
    print(f"   REGIA (da qualsiasi PC o telefono):  {base}/regia")
    print(f"   Su questo PC:                        http://localhost:{PORTA}/regia\n")
    print("   NON chiudere questa finestra finché la mostra è aperta.\n")
    if not SENZA_BROWSER:
        if CONFIG["ruolo"] in PAGINE_RUOLO:
            avvia_postazione()
        else:
            webbrowser.open(f"http://localhost:{PORTA}/regia.html")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        chiudi_postazione()
