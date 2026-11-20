#!/usr/bin/env python3
"""Server locale per il telecomando della TV (Mac / Linux / Windows con Python).

Avvio:  python3 server.py      (sul Mac puoi anche fare doppio clic su avvia-telecomando-mac.command)
"""
import json, os, socket, sys, threading, time, webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
CARTELLA = os.path.dirname(os.path.abspath(__file__))
stato = {"cmd_id": 0, "cmd": "", "tv": None, "tv_t": 0.0}
blocco = threading.Lock()


def ip_locale():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        s.close()


IP = ip_locale()


class Gestore(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=CARTELLA, **k)

    def log_message(self, *a):
        pass  # niente messaggi per ogni richiesta

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, dati):
        corpo = json.dumps(dati).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        with blocco:
            if u.path == "/api/cmd":
                a = (q.get("azione") or [""])[0]
                if a in ("play", "pausa", "toggle", "inizio"):
                    stato["cmd_id"] += 1
                    stato["cmd"] = a
                return self._json({"ok": True, "id": stato["cmd_id"]})
            if u.path == "/api/poll":
                return self._json({"id": stato["cmd_id"], "azione": stato["cmd"]})
            if u.path == "/api/stato":
                eta = int(min(99999, time.time() - stato["tv_t"]))
                return self._json({"eta": eta, "tv": stato["tv"]})
            if u.path == "/api/info":
                return self._json({"ip": IP, "porta": PORTA})
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path == "/api/stato":
            n = min(int(self.headers.get("Content-Length") or 0), 4000)
            try:
                dati = json.loads(self.rfile.read(n) or b"null")
                with blocco:
                    stato["tv"], stato["tv_t"] = dati, time.time()
            except ValueError:
                pass
            return self._json({"ok": True})
        self.send_error(404)


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORTA), Gestore)
    print("\n  ==============================================")
    print("   TELECOMANDO TV ATTIVO")
    print("  ==============================================\n")
    print(f"   Sul PC della TV apri:   http://localhost:{PORTA}/tv.html")
    print(f"   Sul telefono apri:      http://{IP}:{PORTA}/telecomando.html\n")
    print("   Il telefono deve essere sulla STESSA rete Wi-Fi del PC.")
    print("   NON chiudere questa finestra finché la mostra è aperta.\n")
    webbrowser.open(f"http://localhost:{PORTA}/tv.html")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
