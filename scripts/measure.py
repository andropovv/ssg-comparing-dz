"""Замеры для P2: время сборки, объём, Lighthouse, скриншоты.

    python scripts/measure.py builds                      # время сборки и объём → _generated/builds.*
    python scripts/measure.py pages --base URL --label L  # Lighthouse + скриншоты страниц P2 по адресу URL

Таблицы пишутся в docs/_generated/*.md и подключаются в отчёт через pymdownx.snippets,
поэтому цифры в отчёте всегда совпадают с последним прогоном.
"""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_build" / "site" / "p2"
GEN = ROOT / "docs" / "_generated"
IMG = ROOT / "docs" / "img"
RAW = ROOT / "_build" / "measure"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
LIGHTHOUSE = "lighthouse@12.8.2"

BUILDS = {
    "mkdocs": (["mkdocs", "build", "--strict", "-q", "-f", "p2/mkdocs/mkdocs.yml"], ROOT),
    "sphinx": (["sphinx-build", "-q", "-W", "-b", "html", "p2/sphinx", str(OUT / "sphinx")], ROOT),
    "pelican": (["pelican", "-q", "-s", "pelicanconf.py", "--fatal", "warnings"], ROOT / "p2" / "pelican"),
}
TITLES = {"mkdocs": "MkDocs Material", "sphinx": "Sphinx + MyST", "pelican": "Pelican"}


def run_build(name: str) -> float:
    cmd, cwd = BUILDS[name]
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.perf_counter() - t0


def dir_stats(path: Path) -> tuple[int, int]:
    files = [p for p in path.rglob("*") if p.is_file() and ".doctrees" not in p.parts]
    return len(files), sum(p.stat().st_size for p in files)


def measure_builds(repeats: int) -> None:
    rows = {}
    for name in BUILDS:
        cold, warm = [], []
        for _ in range(repeats):
            shutil.rmtree(OUT / name, ignore_errors=True)
            cold.append(run_build(name))
            warm.append(run_build(name))  # повторная сборка без изменений (инкрементальная, где есть)
        n_files, size = dir_stats(OUT / name)
        html = (OUT / name / "index.html").stat().st_size
        rows[name] = {"cold_s": statistics.median(cold), "cold_min_s": min(cold), "cold_max_s": max(cold),
                      "warm_s": statistics.median(warm), "files": n_files, "size_bytes": size, "html_bytes": html}
        print(name, rows[name], file=sys.stderr)

    (GEN / "builds.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    lines = ["| Генератор | Холодная сборка, с (медиана) | min–max, с | Повторная сборка, с | Файлов | Объём результата, КБ | index.html, КБ |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name, r in rows.items():
        lines.append(f"| {TITLES[name]} | {r['cold_s']:.2f} | {r['cold_min_s']:.2f}–{r['cold_max_s']:.2f} | "
                     f"{r['warm_s']:.2f} | {r['files']} | {r['size_bytes'] / 1024:.0f} | {r['html_bytes'] / 1024:.0f} |")
    lines.append(f"\nЗамер: {repeats} прогонов, `{sys.platform}`, Python {sys.version.split()[0]}.")
    (GEN / "builds.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def lighthouse(url: str, preset: str, dest: Path) -> dict:
    cmd = ["npx", "-y", LIGHTHOUSE, url, "--quiet", "--output=json", f"--output-path={dest}",
           "--only-categories=performance,accessibility,best-practices,seo",
           "--chrome-flags=--headless=new --no-sandbox"]
    if preset == "desktop":
        cmd.append("--preset=desktop")
    subprocess.run(cmd, check=True, env={**os.environ, "CHROME_PATH": CHROME})
    return json.loads(dest.read_text(encoding="utf-8"))


def summarize(report: dict) -> dict:
    audits = report["audits"]
    page_host = urlparse(report["finalDisplayedUrl"]).hostname
    requests = audits["network-requests"]["details"]["items"]
    external = sorted({urlparse(r["url"]).hostname for r in requests
                       if urlparse(r["url"]).hostname not in (page_host, None)})
    return {
        **{k: round(v["score"] * 100) for k, v in report["categories"].items()},
        "bytes": audits["total-byte-weight"]["numericValue"],
        "requests": len(requests),
        "external_requests": sum(1 for r in requests if urlparse(r["url"]).hostname not in (page_host, None)),
        "external_hosts": external,
        "lcp_ms": audits["largest-contentful-paint"]["numericValue"],
        "viewport_ok": audits["viewport"]["score"] == 1,
    }


def screenshot_mobile(url: str, dest: Path) -> None:
    # --window-size в headless Chrome меняет окно, но не эмулирует мобильный viewport (DPR, meta viewport):
    # страница рендерится шире экрана и обрезается справа. Playwright эмулирует устройство целиком.
    subprocess.run(["npx", "-y", "playwright@1.56.1", "screenshot", "--channel", "chrome", "--device", "Pixel 7",
                    "--full-page", "--wait-for-timeout", "4000", url, str(dest)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def screenshot(url: str, dest: Path, width: int, height: int) -> None:
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={width},{height}", "--virtual-time-budget=10000",
                    f"--screenshot={dest}", url],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def measure_pages(base: str, label: str, shots: bool, repeats: int) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    rows = {}
    for name in TITLES:
        url = f"{base.rstrip('/')}/p2/{name}/"
        rows[name] = {}
        for preset in ("mobile", "desktop"):
            # Оценка Performance между прогонами плавает на ±20 пунктов, поэтому берём медиану.
            runs = [summarize(lighthouse(url, preset, RAW / f"lh-{label}-{name}-{preset}-{i}.json"))
                    for i in range(repeats)]
            rows[name][preset] = {k: (statistics.median(r[k] for r in runs) if isinstance(v, (int, float))
                                      and not isinstance(v, bool) else v) for k, v in runs[0].items()}
            rows[name][preset]["performance_runs"] = [r["performance"] for r in runs]
            print(name, preset, rows[name][preset], file=sys.stderr)
        if shots:
            screenshot_mobile(url, IMG / f"p2-{name}-mobile.png")
            screenshot(url, IMG / f"p2-{name}-desktop.png", 1280, 3800)

    (GEN / f"lighthouse-{label}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["| Генератор | Режим | Performance (медиана; прогоны) | Accessibility | Best Practices | SEO | Вес страницы, КБ | Запросов | Внешних запросов | LCP, мс |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, by_preset in rows.items():
        for preset, r in by_preset.items():
            runs = ", ".join(str(x) for x in r["performance_runs"])
            lines.append(f"| {TITLES[name]} | {preset} | {r['performance']:.0f} ({runs}) | {r['accessibility']:.0f} | "
                         f"{r['best-practices']:.0f} | {r['seo']:.0f} | {r['bytes'] / 1024:.0f} | {r['requests']:.0f} | "
                         f"{r['external_requests']:.0f} | {r['lcp_ms']:.0f} |")
    lines.append(f"\nАдрес: `{base}`. Lighthouse {LIGHTHOUSE.split('@')[1]}, mobile — эмуляция Moto G Power "
                 "с замедлением сети и CPU, desktop — `--preset=desktop`.")
    (GEN / f"lighthouse-{label}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("builds")
    b.add_argument("--repeats", type=int, default=5)
    p = sub.add_parser("pages")
    p.add_argument("--base", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--shots", action="store_true")
    p.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()
    GEN.mkdir(parents=True, exist_ok=True)
    if args.cmd == "builds":
        measure_builds(args.repeats)
    else:
        measure_pages(args.base, args.label, args.shots, args.repeats)


if __name__ == "__main__":
    main()
