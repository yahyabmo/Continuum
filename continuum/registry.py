"""Every public number comes from results/, never from a hand-typed table.

python -m continuum.registry rewrites the results block of the README; the tests fail
if that block and results/ disagree, or if a measure appears anywhere else.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

START = "<!-- résultats : début -->"
END = "<!-- résultats : fin -->"
MEASURE = re.compile(r"\d+(?:[.,]\d+)?\s?(?:dB|%)")
NONE = "Aucun résultat publié pour l'instant."


def number(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}".replace(".", ",")


def t1_table(report: dict) -> str:
    lines = [
        "| Clip | Images notées | PSNR-M fondu | PSNR-M RIFE | EPE-M fondu | EPE-M RIFE | Validé |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["rows"]:
        psnr, epe = row["psnr_m"], row["epe_m"]
        cells = [
            row["clip"],
            str(row["scored"]),
            number(psnr["crossfade"]),
            number(psnr["rife"]),
            number(epe["crossfade"]),
            number(epe["rife"]),
            "oui" if row["validated"] else "non",
        ]
        lines.append("| " + " | ".join(cells) + " |")
    v = report["verdict"]
    outcome = "réussi" if v["passed"] else "échoué"
    lines += [
        "",
        f"T1 : {v['validated']} clips validés sur {v['clips']}, seuil de 4 sur 6, {outcome}. "
        f"Commit `{report['commit']}`. Une seule personne filmée : rien ne se généralise.",
    ]
    return "\n".join(lines)


def render(results: Path) -> str:
    t1 = results / "t1.json"
    if not t1.exists():
        return NONE
    return "### T1 : RIFE contre le fondu\n\n" + t1_table(json.loads(t1.read_text("utf-8")))


def split(text: str) -> tuple[str, str, str]:
    head, rest = text.split(START, 1)
    block, tail = rest.split(END, 1)
    return head, block.strip(), tail


def stray_measures(text: str) -> list[str]:
    head, _, tail = split(text)
    return MEASURE.findall(head + tail)


def update(readme: Path, results: Path) -> None:
    head, _, tail = split(readme.read_text(encoding="utf-8"))
    body = f"{head}{START}\n{render(results)}\n{END}{tail}"
    readme.write_text(body, encoding="utf-8")


if __name__ == "__main__":
    update(Path("README.md"), Path("results"))
