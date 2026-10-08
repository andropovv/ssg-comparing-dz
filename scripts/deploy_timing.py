"""Время развёртывания на Helios по rsync: полный, без изменений, после правки одного файла.

    python scripts/deploy_timing.py --key ~/.ssh/itmo/helios_deploy

Деплой идёт во временный каталог ~/public_html/ssg-timing/, который в конце удаляется,
поэтому рабочий сайт ~/public_html/ssg/ не затрагивается. Результат — docs/_generated/deploy.md.
"""

import argparse
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_build" / "site"
HOST, PORT, USER = "helios.cs.ifmo.ru", "2222", "s487249"
TARGET = "public_html/ssg-timing"


def ssh_cmd(key: str) -> str:
    return f"ssh -p {PORT} -i {key} -o IdentitiesOnly=yes -o BatchMode=yes"


def rsync(key: str) -> tuple[float, str]:
    t0 = time.perf_counter()
    out = subprocess.run(["rsync", "-az", "--delete", "--stats", "-e", ssh_cmd(key), f"{SITE}/", f"{USER}@{HOST}:{TARGET}/"],
                         check=True, capture_output=True, text=True).stdout
    return time.perf_counter() - t0, out


def remote(key: str, command: str) -> None:
    subprocess.run(ssh_cmd(key).split() + [f"{USER}@{HOST}", command], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()

    files = sum(1 for p in SITE.rglob("*") if p.is_file())
    size = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
    marker = SITE / "index.html"
    original = marker.read_bytes()

    full, noop, one = [], [], []
    try:
        for _ in range(args.repeats):
            remote(args.key, f"rm -rf ~/{TARGET}")
            full.append(rsync(args.key)[0])
            noop.append(rsync(args.key)[0])
            marker.write_bytes(original + f"<!-- {time.time()} -->".encode())
            one.append(rsync(args.key)[0])
            marker.write_bytes(original)
    finally:
        marker.write_bytes(original)
        remote(args.key, f"rm -rf ~/{TARGET}")

    lines = ["| Сценарий | Время, с (медиана) | min–max, с |", "|---|---:|---:|"]
    for name, xs in (("Полный деплой в пустой каталог", full), ("Повторный, без изменений", noop),
                     ("Изменён один HTML-файл", one)):
        lines.append(f"| {name} | {statistics.median(xs):.1f} | {min(xs):.1f}–{max(xs):.1f} |")
    lines.append(f"\nrsync по SSH с рабочей машины разработчика на helios.cs.ifmo.ru:2222; сайт — {files} файлов, "
                 f"{size / 2**20:.1f} МБ; {args.repeats} прогона. rsync передаёт только изменившиеся файлы, "
                 "поэтому повторный деплой определяется временем SSH-рукопожатия и сравнения списков файлов.")
    (ROOT / "docs" / "_generated" / "deploy.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
