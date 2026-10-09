# Ход работы

## Окружение

| Компонент | Версия |
|---|---|
| ОС разработчика | macOS 26.2 (Darwin 25.2, arm64) |
| Python | 3.14.2 (python.org) |
| pip | 25.3 системный, 26.2.1 в venv |
| virtualenv | 21.14.6 |
| Node.js | 24.12.0 (только для Lighthouse и Playwright при замерах) |
| CI | GitHub Actions, `ubuntu-latest`, Python 3.14 |
| Хостинг | GitHub Pages; Helios ИТМО (FreeBSD 14.5, nginx 1.30) |

## 1. Python, pip, virtualenv

```console
$ python3 --version
Python 3.14.2
$ pip3 --version
pip 25.3 from /Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/pip (python 3.14)
$ virtualenv --version
zsh: command not found: virtualenv
$ python3 -m pip install --user virtualenv
$ python3 -m virtualenv --version
virtualenv 21.14.6 from ~/Library/Python/3.14/lib/python/site-packages/virtualenv/__init__.py
```

## 2. Каталог проекта и виртуальное окружение

```console
$ mkdir -p itmo-python/1 && cd itmo-python/1
$ python3 -m virtualenv .venv
$ source .venv/bin/activate
(.venv) $ python --version
Python 3.14.2
```

## 3. Зависимости

Выбран `requirements.txt` с точными версиями всего дерева (`pip freeze`, 80 пакетов): ставится одной
командой `pip install -r requirements.txt` и в CI, и локально. Отдельно закреплён `mkdocs==1.6.1`:
при каждой сборке Material печатает предупреждение, что MkDocs 2.0 удаляет систему плагинов и тем.

```console
(.venv) $ pip install mkdocs-material mkdocs-bibtex sphinx myst-parser sphinxcontrib-bibtex \
                      sphinx-design furo pelican matplotlib plotly pandas
(.venv) $ pip freeze > requirements.txt
```

`.gitignore` исключает виртуальное окружение, каталоги сборки (`_build/`, `site/`), копии общих
ассетов в исходниках генераторов и кэши (`__pycache__/`, `.cache/`, кэш Pelican).

## 4. Каркас сайта и локальная сборка

`mkdocs.yml` написан вручную, без `mkdocs new`: тема Material, `language: ru`, поиск с `lang: [ru, en]`,
`site_url` из переменной окружения, `strict: true`.

```console
(.venv) $ mkdocs serve            # предпросмотр на http://127.0.0.1:8000 с live reload
(.venv) $ mkdocs build --strict
--8<-- "_generated/mkdocs-build.txt"
```

Полная сборка (отчёт и три страницы P2) — `./scripts/build_all.sh`, см. [CI/CD](ci.md).

Структура репозитория:

```text
.
├── .github/
│   ├── workflows/deploy.yml   # сборка → GitHub Pages + Helios → проверка
│   └── helios_known_hosts     # закреплённый ключ хоста Helios
├── docs/                      # этот отчёт (MkDocs Material)
│   ├── _generated/            # таблицы замеров, пишутся скриптами
│   └── img/                   # скриншоты
├── p2/
│   ├── shared/                # make_figures.py, refs.bib, vendor/tex-svg.js (MathJax), favicon
│   ├── mkdocs/                # стресс-страница: MkDocs Material
│   ├── sphinx/                # стресс-страница: Sphinx + MyST
│   └── pelican/               # стресс-страница: Pelican + свой плагин bibcite
├── scripts/
│   ├── build_all.sh           # сборка всего в _build/site
│   ├── check_site.py          # проверка развёрнутого сайта
│   ├── measure.py             # время сборки, Lighthouse, скриншоты
│   ├── scale_test.py          # T1: сборка 300 страниц
│   └── t1_matrix.py           # T1: взвешенная матрица и профили весов
├── mkdocs.yml
├── requirements.txt
├── LICENSE                    # MIT — код
└── LICENSE-CONTENT.md         # CC BY 4.0 — тексты, рисунки, данные
```

## 5. Репозиторий и GitHub Actions

```console
$ git init -b main && git add . && git commit -m "Lab 1: SSG comparison, P2 stress test, CI/CD"
$ git remote add origin git@github.com:andropovv/ssg-comparing-dz.git && git push -u origin main
```

В настройках репозитория: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
Разница между публикацией через ветку `gh-pages` и через артефакт разобрана в
[CI/CD](ci.md#два-способа-публикации-на-github-pages).

## 6. Helios

Аккаунт `s487249` уже был активен: пароль выдаётся на `se.ifmo.ru/passwd` после входа через ИТМО ID.
Для CI создан отдельный ключ, пароль используется только один раз — при установке ключа:

```console
$ ssh-keygen -t ed25519 -N "" -C "github-actions-deploy-helios" -f ~/.ssh/itmo/helios_deploy
$ ssh -p 2222 s487249@helios.cs.ifmo.ru 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys' < ~/.ssh/itmo/helios_deploy.pub
$ ssh -p 2222 -i ~/.ssh/itmo/helios_deploy s487249@helios.cs.ifmo.ru uname -sr
FreeBSD 14.5-STABLE
$ ssh-keyscan -p 2222 -t ed25519 helios.cs.ifmo.ru > .github/helios_known_hosts
```

Приватный ключ добавлен в секрет репозитория `HELIOS_SSH_KEY`.

## 7. Базовый URL

| Площадка | `SITE_URL` | Адрес отчёта |
|---|---|---|
| Локально | `http://localhost:8000/` | — |
| GitHub Pages | `steps.pages.outputs.base_url` из `actions/configure-pages` | <https://andropovv.github.io/ssg-comparing-dz/> |
| Helios | `https://se.ifmo.ru/~s487249/ssg/` | <https://se.ifmo.ru/~s487249/ssg/> |

`site_url: !ENV [SITE_URL, ...]` в `mkdocs.yml` читает переменную окружения. P2-страница MkDocs
получает `${SITE_URL}p2/mkdocs/`. Почему нужны две сборки, а не одна — в [CI/CD](ci.md#базовый-url-что-ломается-в-подкаталоге).

## 8. Проверка результата

Не визуально, а скриптом `scripts/check_site.py`: код ответа, контрольная строка, поисковые индексы,
отсутствие внешних CDN, рендер формул при заблокированной сети. Подробности и вывод — в
[CI/CD](ci.md#проверка-развёртывания).

## 9. Лицензии

Раздельно: код — MIT (`LICENSE`), контент — CC BY 4.0 (`LICENSE-CONTENT.md`). Подробнее — на
странице [Лицензии](license.md).
