# /// script
# requires-python = ">=3.10"
# ///
"""Cobertura del guion (fase 5 del modo UGC): qué escena de la marca está en qué toma.

Uso:
    uv run cobertura.py <carpeta del vídeo>

Lee 06_entrega/trabajo/guion.json (lo escribe Claude a partir de la ficha de campaña):
    {"escenas": [
       {"id": "1A", "grupo": "gancho", "nombre": "Gancho A", "texto": "…", "literal": false},
       {"id": "3",  "nombre": "Producto", "texto": "…", "literal": true}
     ],
     "prohibidas": ["barata", "low cost"]}
- "grupo": escenas alternativas (p. ej. 3 ganchos): cada una es una versión del vídeo.
- "literal": la frase se tiene que decir tal cual (se avisa de cada palabra distinta).
- "prohibidas": palabras o expresiones que no pueden salir (también en plural o con tilde).

Y transcripcion.json (de transcribir.py). Escribe en 06_entrega/trabajo/:
    cobertura.json   la mejor toma de cada escena (clip, inicio, fin) y los problemas
    cobertura.md     la tabla para el talento

Mejor toma: la que más se parece a la frase del guion, sin palabras prohibidas; a igualdad, la
última. Códigos: 0 todo cubierto · 2 falta una escena o solo hay tomas con palabras prohibidas.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UMBRAL = 0.55        # parecido mínimo para contar como toma de una escena
LITERAL_OK = 0.97    # en escenas literales, por debajo se avisa de las diferencias


def norm(t: str) -> str:
    s = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in s if c.isalnum() or c in " %")


def fichas(texto: str) -> list[str]:
    return [x for x in norm(texto).replace("%", " %").split() if x]


def mmss(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}"


def ventanas(clip: dict):
    """Todas las secuencias seguidas de palabras de un clip (con su texto normalizado)."""
    ws = [w for f in clip["frases"] for w in f["palabras"]]
    tok = []
    for i, w in enumerate(ws):
        for t in fichas(w["p"]):
            tok.append((t, i))
    return ws, tok


def mejor_en_clip(objetivo: list[str], ws: list[dict], tok: list[tuple[str, int]]):
    n = len(objetivo)
    mejor = None
    for largo in sorted({max(1, round(n * f)) for f in (0.7, 0.85, 1.0, 1.15, 1.3)}):
        for i in range(0, max(1, len(tok) - largo + 1)):
            trozo = [t for t, _ in tok[i:i + largo]]
            r = SequenceMatcher(None, objetivo, trozo).ratio()
            if mejor is None or r > mejor[0]:
                mejor = (r, i, i + largo)
    if mejor is None:
        return None
    r, a, b = mejor
    wa, wb = tok[a][1], tok[min(b, len(tok)) - 1][1]
    tramo = ws[wa:wb + 1]
    return {"parecido": round(r, 3), "inicio": tramo[0]["inicio"], "fin": tramo[-1]["fin"],
            "dicho": " ".join(w["p"] for w in tramo), "fichas": [t for t, _ in tok[a:b]],
            "claridad": round(sum(w.get("prob", 1) for w in tramo) / len(tramo), 3)}


def prohibidas_en(fichas_dichas: list[str], prohibidas: list[str]) -> list[str]:
    encontradas = []
    for p in prohibidas:
        objetivo = fichas(p)
        for i in range(len(fichas_dichas) - len(objetivo) + 1):
            trozo = fichas_dichas[i:i + len(objetivo)]
            # «barata» también encuentra «baratas» y «baratísima»
            if all(t.startswith(o[:max(4, len(o) - 1)]) for t, o in zip(trozo, objetivo)):
                encontradas.append(p)
                break
    return encontradas


def diferencias(objetivo: list[str], dicho: list[str]) -> str:
    partes = []
    for op, a1, a2, b1, b2 in SequenceMatcher(None, objetivo, dicho).get_opcodes():
        if op == "replace":
            partes.append(f"«{' '.join(objetivo[a1:a2])}» → «{' '.join(dicho[b1:b2])}»")
        elif op == "delete":
            partes.append(f"falta «{' '.join(objetivo[a1:a2])}»")
        elif op == "insert":
            partes.append(f"sobra «{' '.join(dicho[b1:b2])}»")
    return "; ".join(partes)


def main() -> int:
    p = argparse.ArgumentParser(description="Cobertura del guion de la marca en los brutos.")
    p.add_argument("carpeta", type=Path)
    args = p.parse_args()
    trabajo = args.carpeta.resolve() / "06_entrega" / "trabajo"
    for f in ("guion.json", "transcripcion.json"):
        if not (trabajo / f).exists():
            print(f"Falta {trabajo / f}." + (" Escríbelo a partir de la ficha de campaña." if f == "guion.json"
                                               else " Antes transcribe los brutos con transcribir.py."))
            return 2
    guion = json.loads((trabajo / "guion.json").read_text(encoding="utf-8"))
    trans = json.loads((trabajo / "transcripcion.json").read_text(encoding="utf-8"))
    prohibidas = guion.get("prohibidas", [])
    clips = [(c["archivo"], *ventanas(c)) for c in trans["clips"]]

    escenas, problemas_graves = [], 0
    for e in guion["escenas"]:
        objetivo = fichas(e["texto"])
        candidatas = []
        for archivo, ws, tok in clips:
            m = mejor_en_clip(objetivo, ws, tok) if tok else None
            if m and m["parecido"] >= UMBRAL:
                m["clip"] = archivo
                m["prohibidas"] = prohibidas_en(m["fichas"], prohibidas)
                candidatas.append(m)
        limpias = [c for c in candidatas if not c["prohibidas"]]
        orden = lambda c: (round(c["parecido"], 2), c["claridad"], candidatas.index(c))
        res = {"id": e["id"], "nombre": e.get("nombre", ""), "grupo": e.get("grupo"), "texto": e["texto"],
               "literal": e.get("literal", False), "tomas": len(candidatas), "notas": []}
        if not candidatas:
            res["estado"] = "falta"
            res["notas"].append("No se ha grabado: hay que grabarla antes de editar.")
            problemas_graves += 1
        else:
            elegida = max(limpias or candidatas, key=orden)
            res["toma"] = {"clip": elegida["clip"], "inicio": elegida["inicio"], "fin": elegida["fin"]}
            res["parecido"] = elegida["parecido"]
            res["claridad"] = elegida["claridad"]
            res["dicho"] = elegida["dicho"]
            res["estado"] = "ok"
            for c in candidatas:
                if c["prohibidas"]:
                    res["notas"].append(f"{Path(c['clip']).name} {mmss(c['inicio'])} dice «{', '.join(c['prohibidas'])}» "
                                        f"(prohibida): {'se usa otra toma' if limpias else 'no hay otra toma'}.")
            if not limpias:
                res["estado"] = "regrabar"
                res["notas"].append("Todas las tomas tienen palabras prohibidas: hay que regrabar (o cortarla si no "
                                    "cambia el sentido).")
                problemas_graves += 1
            if e.get("literal") and elegida["parecido"] < LITERAL_OK:
                res["estado"] = res["estado"] if res["estado"] != "ok" else "aviso"
                res["notas"].append("Literal, pero no se dice igual: " + diferencias(objetivo, elegida["fichas"]))
            if elegida["claridad"] < 0.6:
                res["estado"] = res["estado"] if res["estado"] != "ok" else "aviso"
                res["notas"].append("Se oye poco claro (audio o dicción): revísala.")
        escenas.append(res)

    (trabajo / "cobertura.json").write_text(json.dumps({"escenas": escenas, "prohibidas": prohibidas},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    simbolo = {"ok": "✓", "aviso": "⚠", "regrabar": "✗", "falta": "✗"}
    filas = ["# Cobertura del guion", "",
             "| Escena | Frase del guion | Mejor toma (clip + segundo) | ¿Dice lo exigido? | Calidad | Problema |",
             "|---|---|---|---|---|---|"]
    for r in escenas:
        toma = f"{Path(r['toma']['clip']).name} · {mmss(r['toma']['inicio'])}–{mmss(r['toma']['fin'])}" if "toma" in r else "—"
        exigido = ("—" if "toma" not in r else
                   ("Sí" if not r["literal"] or r.get("parecido", 0) >= LITERAL_OK else "No igual") +
                   f" ({round(r.get('parecido', 0) * 100)} %)")
        calidad = "—" if "toma" not in r else ("buena" if r["claridad"] >= 0.8 else "regular" if r["claridad"] >= 0.6 else "mala")
        filas.append(f"| {simbolo[r['estado']]} {r['id']} · {r['nombre']} | {r['texto']} | {toma} | {exigido} | {calidad} | "
                     f"{' '.join(r['notas']) or '—'} |")
    (trabajo / "cobertura.md").write_text("\n".join(filas) + "\n", encoding="utf-8")
    for r in escenas:
        print(f"  {simbolo[r['estado']]} {r['id']} {r['nombre']}: " +
              (f"{Path(r['toma']['clip']).name} {mmss(r['toma']['inicio'])} ({round(r['parecido'] * 100)} %)" if "toma" in r else "sin grabar") +
              (f" — {' '.join(r['notas'])}" if r["notas"] else ""))
    print(f"  {trabajo / 'cobertura.md'}")
    return 2 if problemas_graves else 0


if __name__ == "__main__":
    sys.exit(main())
