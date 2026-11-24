"""Sirve una carpeta por http (solo en este ordenador) con soporte de saltos en los vídeos (Range).

El `python -m http.server` normal no deja saltar dentro de un vídeo: los botones ▶ de los storyboards y
«Así quedaría» empiezan siempre desde el principio. Este sí.

Uso:
  python servir.py --carpeta 06_trabajo [--puerto 8771] [--abrir storyboard-corte.html]
"""
import argparse
import http.server
import os
import re
import webbrowser
from functools import partial


class Manejador(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        rango = self.headers.get("Range")
        ruta = self.translate_path(self.path)
        m = re.match(r"bytes=(\d*)-(\d*)$", rango or "")
        if not m or not os.path.isfile(ruta):
            return super().send_head()
        total = os.path.getsize(ruta)
        ini = int(m.group(1)) if m.group(1) else max(total - int(m.group(2) or 0), 0)
        fin = int(m.group(2)) if m.group(1) and m.group(2) else total - 1
        fin = min(fin, total - 1)
        if ini >= total:
            self.send_error(416)
            return None
        f = open(ruta, "rb")
        f.seek(ini)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(ruta))
        self.send_header("Content-Range", f"bytes {ini}-{fin}/{total}")
        self.send_header("Content-Length", str(fin - ini + 1))
        self.end_headers()
        self._quedan = fin - ini + 1
        return f

    def copyfile(self, origen, destino):
        quedan = getattr(self, "_quedan", None)
        try:
            if quedan is None:
                return super().copyfile(origen, destino)
            while quedan > 0:
                b = origen.read(min(1 << 16, quedan))
                if not b:
                    break
                destino.write(b)
                quedan -= len(b)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass   # el navegador corta la descarga al saltar: es normal
        finally:
            self._quedan = None

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", required=True)
    ap.add_argument("--puerto", type=int, default=8771)
    ap.add_argument("--abrir", help="Página que se abre en el navegador del usuario")
    a = ap.parse_args()
    # En Windows, con allow_reuse_address dos servidores pueden ocupar el mismo puerto y el navegador
    # acaba en el otro (página «no encontrada»). Sin él, si el puerto está ocupado se prueba el siguiente.
    class Servidor(http.server.ThreadingHTTPServer):
        allow_reuse_address = False

    for puerto in range(a.puerto, a.puerto + 20):
        try:
            srv = Servidor(("127.0.0.1", puerto), partial(Manejador, directory=a.carpeta))
            break
        except OSError:
            continue
    else:
        raise SystemExit(f"Los puertos {a.puerto}-{a.puerto + 19} están ocupados.")
    url = f"http://127.0.0.1:{puerto}/{a.abrir or ''}"
    print(f"Sirviendo {a.carpeta} en {url}", flush=True)
    if a.abrir:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    main()
