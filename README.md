# ЛР 1. Генераторы статических сайтов на Python

Отчёт (MkDocs Material) и стресс-страница научного контента на трёх генераторах
(MkDocs Material, Sphinx + MyST, Pelican) с автоматическим развёртыванием на GitHub Pages и Helios ИТМО.

- Helios: <https://se.ifmo.ru/~s487249/ssg/>
- GitHub Pages: <https://andropovv.github.io/ssg-comparing-dz/>
- Репозиторий: <https://github.com/andropovv/ssg-comparing-dz>

## Локальная сборка

```bash
python3 -m virtualenv .venv && source .venv/bin/activate
pip install -r requirements.txt
./scripts/build_all.sh                      # → _build/site
python -m http.server 8000 -d _build/site
python scripts/check_site.py http://localhost:8000/
```

## Замеры

```bash
python scripts/measure.py builds                                     # время сборки и объём
python scripts/measure.py pages --base http://localhost:8000 --label local --shots   # Lighthouse + скриншоты (нужны Node и Chrome)
python scripts/scale_test.py --pages 300                             # T1: сборка 300 страниц
python scripts/t1_matrix.py                                          # T1: взвешенная матрица
```

## Настройка CI

1. Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. Settings → Secrets and variables → Actions → New repository secret:
   `HELIOS_SSH_KEY` — приватный ключ, публичная часть которого лежит в `~/.ssh/authorized_keys` на Helios.
3. Push в `main` → сборка → GitHub Pages + Helios → проверка.
4. Проваленный запуск для отчёта: Actions → Build and deploy → Run workflow → `break_build: true`.

## Лицензии

Код — MIT ([LICENSE](LICENSE)), контент — CC BY 4.0 ([LICENSE-CONTENT.md](LICENSE-CONTENT.md)).
