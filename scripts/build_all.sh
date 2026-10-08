#!/usr/bin/env bash
# Сборка всего сайта в _build/site/:
#   /                 — отчёт (MkDocs Material)
#   /p2/mkdocs/       — стресс-страница P2 на MkDocs Material
#   /p2/sphinx/       — та же страница на Sphinx + MyST
#   /p2/pelican/      — та же страница на Pelican
# SITE_URL задаёт абсолютный адрес отчёта (canonical, sitemap, 404.html) под конкретную площадку.
set -euo pipefail
cd "$(dirname "$0")/.."

export SITE_URL="${SITE_URL:-http://localhost:8000/}"
OUT=_build/site

python p2/shared/make_figures.py >/dev/null

# Основной сайт собирается первым: mkdocs build очищает site_dir целиком.
mkdocs build --strict --clean -f mkdocs.yml

# Общие артефакты P2 → каталоги исходников генераторов (в git не попадают, см. .gitignore).
for dst in p2/mkdocs/docs/assets p2/pelican/content/assets; do
  mkdir -p "$dst"
  cp p2/shared/build/{phase.png,oscillation.png,plotly.min.js} p2/shared/vendor/{tex-svg.js,favicon.png} "$dst/"
done
cp p2/shared/build/plotly_fragment.html p2/mkdocs/docs/assets/

SITE_URL="${SITE_URL%/}/p2/mkdocs/" mkdocs build --strict --clean -f p2/mkdocs/mkdocs.yml
sphinx-build -q -W --keep-going -b html p2/sphinx "$OUT/p2/sphinx"
(cd p2/pelican && pelican -q -s pelicanconf.py --fatal warnings)

# Helios (nginx) отдаёт только файлы с правами на чтение для всех.
find "$OUT" -type d -exec chmod 755 {} + && find "$OUT" -type f -exec chmod 644 {} +
echo "Built $(find "$OUT" -type f | wc -l | tr -d ' ') files, $(du -sh "$OUT" | cut -f1) → $OUT"
