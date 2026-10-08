"""T1: время холодной и инкрементальной сборки на корпусе из N одинаковых страниц.

    python scripts/scale_test.py --pages 300 --repeats 3

Каждая страница: заголовки, абзацы, формула, листинг, таблица. Проекты создаются во временном
каталоге с минимальной конфигурацией каждого генератора (тема по умолчанию для научного сайта).
Результат — docs/_generated/scale.md.
"""

import argparse
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "docs" / "_generated"

BODY = """
Затухающие колебания описываются уравнением $\\ddot x + 2\\gamma \\dot x + \\omega_0^2 x = 0$.
Страница {i} содержит типичный для отчёта набор элементов: текст, формулу, таблицу и листинг.

## Методика {i}

$$
x(t) = A e^{{-\\gamma t}} \\cos(\\omega t + \\varphi)
$$

| Серия | γ | ω |
|---|---|---|
| {i}.1 | 0,15 | 3,14 |
| {i}.2 | 0,30 | 3,14 |

```python
def model(t, a, gamma, omega, phi):
    return a * np.exp(-gamma * t) * np.cos(omega * t + phi)
```

## Результаты {i}

{lorem}
"""
LOREM = ("Оценки параметров получены методом наименьших квадратов по огибающей сигнала. " * 12).strip()


def page(i: int) -> str:
    return BODY.format(i=i, lorem=LOREM)


def setup_mkdocs(d: Path, n: int) -> list[str]:
    (d / "docs").mkdir(parents=True)
    (d / "mkdocs.yml").write_text(
        "site_name: scale\ntheme:\n  name: material\n  language: ru\n  font: false\n"
        "plugins:\n  - search:\n      lang: ru\n"
        "markdown_extensions:\n  - tables\n  - pymdownx.arithmatex:\n      generic: true\n"
        "  - pymdownx.highlight\n  - pymdownx.superfences\n", encoding="utf-8")
    (d / "docs" / "index.md").write_text("# Корпус\n", encoding="utf-8")
    for i in range(n):
        (d / "docs" / f"p{i:04d}.md").write_text(f"# Страница {i}\n" + page(i), encoding="utf-8")
    return ["mkdocs", "build", "-q", "-d", "out"]


def setup_sphinx(d: Path, n: int) -> list[str]:
    d.mkdir(parents=True)
    (d / "conf.py").write_text(
        "project='scale'\nlanguage='ru'\nextensions=['myst_parser']\n"
        "myst_enable_extensions=['dollarmath']\nhtml_theme='furo'\n", encoding="utf-8")
    (d / "index.md").write_text("# Корпус\n\n```{toctree}\n:glob:\n\np*\n```\n", encoding="utf-8")
    for i in range(n):
        (d / f"p{i:04d}.md").write_text(f"# Страница {i}\n" + page(i), encoding="utf-8")
    return ["sphinx-build", "-q", "-b", "html", ".", "out"]


def setup_pelican(d: Path, n: int) -> list[str]:
    (d / "content" / "pages").mkdir(parents=True)
    (d / "pelicanconf.py").write_text(
        "SITENAME='scale'\nPATH='content'\nOUTPUT_PATH='out'\nTIMEZONE='Europe/Moscow'\nDEFAULT_LANG='ru'\n"
        "FEED_ALL_ATOM=None\nCATEGORY_FEED_ATOM=None\nAUTHOR_FEED_ATOM=None\nAUTHOR_FEED_RSS=None\n"
        "TRANSLATION_FEED_ATOM=None\nRELATIVE_URLS=True\n"
        # Кэш разобранного контента: без него Pelican всегда пересобирает всё.
        "CACHE_CONTENT=True\nLOAD_CONTENT_CACHE=True\n", encoding="utf-8")
    for i in range(n):
        (d / "content" / "pages" / f"p{i:04d}.md").write_text(
            f"Title: Страница {i}\nSlug: p{i:04d}\n" + page(i), encoding="utf-8")
    return ["pelican", "-q", "-s", "pelicanconf.py"]


SETUPS = {"MkDocs Material": (setup_mkdocs, "docs/p0007.md"),
          "Sphinx + MyST": (setup_sphinx, "p0007.md"),
          "Pelican": (setup_pelican, "content/pages/p0007.md")}


def timed(cmd: list[str], cwd: Path) -> float:
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.perf_counter() - t0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=300)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()

    rows = []
    for name, (setup, edited) in SETUPS.items():
        cold, noop, inc = [], [], []
        for _ in range(args.repeats):
            with tempfile.TemporaryDirectory() as tmp:
                d = Path(tmp) / "proj"
                cmd = setup(d, args.pages)
                cold.append(timed(cmd, d))
                noop.append(timed(cmd, d))
                with open(d / edited, "a", encoding="utf-8") as f:
                    f.write("\nДобавленный абзац для проверки инкрементальной сборки.\n")
                inc.append(timed(cmd, d))
                out = d / "out"
                files = [p for p in out.rglob("*") if p.is_file() and ".doctrees" not in p.parts]
                size = sum(p.stat().st_size for p in files)
        rows.append((name, statistics.median(cold), statistics.median(noop), statistics.median(inc), len(files), size))
        print(rows[-1])

    lines = [f"| Генератор | Холодная сборка, с | Без изменений, с | Изменена 1 страница, с | Файлов | Объём, МБ |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, c, n, i, f, s in rows:
        lines.append(f"| {name} | {c:.2f} | {n:.2f} | {i:.2f} | {f} | {s / 2**20:.1f} |")
    lines.append(f"\nКорпус: {args.pages} страниц + index, медиана {args.repeats} прогонов. "
                 "Pelican — с `CACHE_CONTENT` и `LOAD_CONTENT_CACHE`, Sphinx — встроенная инкрементальная "
                 "сборка по doctree, MkDocs пересобирает всё всегда (`--dirty` есть только у `mkdocs serve`).")
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / "scale.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
