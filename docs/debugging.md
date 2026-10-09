# Отладка

Все ошибки ниже возникли на самом деле в ходе работы. Тексты ошибок приведены как есть,
а исправления оставлены в коде с комментариями «почему так».

## 1. Plotly-график пустой

**Ошибка.** На странице MkDocs на месте интерактивного графика пустой блок высотой 360 px.
Сборка `mkdocs build --strict` проходит без предупреждений.

**Гипотеза.** Фрагмент `plotly_fragment.html` содержит inline-скрипт `Plotly.newPlot(...)`, а
`plotly.min.js` подключён через `extra_javascript`, который Material вставляет в конец `<body>`,
то есть после фрагмента. На момент вызова `Plotly` ещё не определён.

**Проверка.** Порядок в HTML: `grep -n "plotly" _build/site/p2/mkdocs/index.html` — inline-скрипт
стоит раньше тега `<script src="assets/plotly.min.js">`. В консоли браузера —
`ReferenceError: Plotly is not defined`.

**Решение.** В `make_figures.py` тело inline-скрипта оборачивается в
`window.addEventListener("DOMContentLoaded", …)`: обычные скрипты в конце `<body>` и `defer`-скрипты
выполняются до этого события. Решение общее для всех трёх генераторов, где бы ни была подключена
библиотека.

## 2. Sphinx: «exactly one table expected»

**Ошибка.**

```text
p2/sphinx/index.md:70: ERROR: Error parsing content block for the "table" directive: exactly one table expected.
p2/sphinx/index.md:86: WARNING: undefined label: 'tbl-params' [ref.numref]
```

**Гипотеза.** Grid-таблица rST разбирается по позициям символов `+` и `|`. Строка с объединённой
ячейкой «Условия: …» оказалась на 7 символов шире остальных, и docutils не распознал таблицу.
Вторая ошибка — следствие первой: таблица не создана, поэтому нет и метки.

**Проверка.** Длина строк: 47 символов у рамки и 54 у последней строки.

**Решение.** Таблица сгенерирована скриптом с явными ширинами столбцов. Вывод для T1: grid-таблицы
— единственный способ объединить ячейки в Sphinx без расширений, но редактировать их руками
неудобно (альтернатива — `flat-table` из linuxdoc).

## 3. Pelican: `--fatal warnings` падает на лентах

**Ошибка.**

```text
WARNING  Feeds generated without SITEURL or FEED_DOMAIN set properly may not be valid
CRITICAL RuntimeError: Warning or error encountered
```

**Гипотеза.** Pelican — блоговый движок, и ленты Atom/RSS по умолчанию включены. Мы отключили
`FEED_ALL_ATOM` и `CATEGORY_FEED_ATOM`, но осталась лента по авторам.

**Проверка.** В `pelican/settings.py` в `DEFAULT_CONFIG` есть `AUTHOR_FEED_ATOM` и `AUTHOR_FEED_RSS`.

**Решение.** `AUTHOR_FEED_ATOM = AUTHOR_FEED_RSS = None`. Сразу после этого появилась следующая ошибка:

```text
ERROR    Skipping .../content/assets/plotly_fragment.html: could not find information about 'title'
```

Pelican считает любой `.html` в `content/` исходником статьи. Исправлено так: фрагмент берётся
snippets'ом из `p2/shared/build`, а в конфиге стоит `READERS = {"html": None}`.

## 4. MkDocs Material: 9 внешних запросов к Google Fonts

**Ошибка.** Lighthouse на странице MkDocs показал 9 внешних запросов, у Sphinx и Pelican — 0.
Требование «работа при недоступности CDN» нарушено.

**Гипотеза.** Тема Material по умолчанию подключает Roboto и Roboto Mono с `fonts.googleapis.com`.

**Проверка.** Список запросов из отчёта Lighthouse (`network-requests`): 1 CSS с
`fonts.googleapis.com` и 8 `woff2` с `fonts.gstatic.com`. Замер «до» сохранён в
`docs/_generated/lighthouse-local-before-privacy.md`.

**Решение, попытка 1.** Встроенный плагин `privacy` скачивает внешние ресурсы при сборке.
Шрифты стали локальными, но плагин просканировал и `plotly.min.js` и скачал всё, что нашёл
внутри по URL: `unpkg.com/mermaid@11`, стили карт `basemaps.cartocdn.com`, `geoserveis.icgc.cat`.
Это +4,7 МБ в `assets/external/`, к тому же переписаны URL внутри plotly.js.

**Решение, попытка 2 (принято).** `theme.font: false` — системные шрифты, 0 внешних запросов,
сборке не нужна сеть.

--8<-- "_generated/lighthouse-local-before-privacy.md"

## 5. Snippets не находит файл при сборке из корня

**Ошибка.**

```text
pymdownx.snippets.SnippetMissingError: Snippet at path 'assets/plotly_fragment.html' could not be found
```

**Гипотеза.** Из каталога `p2/mkdocs/` сборка проходила, из корня репозитория — нет. Значит,
`base_path: [docs]` считается от текущего каталога процесса, а не от `mkdocs.yml`.

**Проверка.** `cd p2/mkdocs && mkdocs build` — успех; `mkdocs build -f p2/mkdocs/mkdocs.yml` — ошибка.

**Решение.** `base_path: !relative $docs_dir`: тег `!relative` в MkDocs ≥ 1.5 привязывает путь к
конфигурации. В CI сборка всегда идёт из корня, так что без исправления workflow падал бы.

## 6. Якорь `#_1` вместо `#литература`

**Ошибка.** В оглавлении MkDocs ссылка на раздел «Литература» имела вид `#_1`.

**Гипотеза.** Стандартный `slugify` из Python-Markdown оставляет только ASCII, кириллица
выбрасывается целиком, и вместо пустого id подставляется `_1`.

**Проверка.** `grep 'href="#_1"' index.html`. Для двух русских заголовков без явного id
получились бы `_1` и `_2`. Эти якоря меняются при перестановке разделов, и внешние ссылки на
них ломаются.

**Решение.** В отчёте — `toc.slugify: pymdownx.slugs.slugify` с сохранением Unicode. На страницах
P2 — явные id `{#method}`, одинаковые для всех генераторов.

## 7. Pelican: в списке литературы одна запись из трёх

**Ошибка.** Свой плагин `bibcite` выводил в «Литературе» только Harris (2020), хотя в тексте были
три ссылки [1]–[3].

**Гипотеза.** `style.format_entries()` из pybtex обходит переданную последовательность дважды:
сначала для меток, потом для текста. А передавался генератор, который исчерпывается после
первого прохода.

**Проверка.** В REPL тот же вызов с генератором вернул одну запись, со списком — три.

**Решение.** `format_entries([bib.entries[k] for k in order])`, в коде оставлен комментарий.

## 8. Helios: Best Practices 75 и mixed content

**Ошибка.** На Helios у Sphinx и Pelican «Best Practices» 75 против 96–100 локально:

```text
Mixed Content: The page at 'https://se.ifmo.ru/~s487249/ssg/p2/sphinx/' was loaded over HTTPS,
but requested an insecure favicon 'http://se.ifmo.ru/o/favicon/'.
```

**Гипотеза.** У этих страниц нет `<link rel="icon">`, поэтому браузер запрашивает `/favicon.ico` в
корне домена. Корень `se.ifmo.ru` принадлежит не нам и перенаправляет на `http://`.
У MkDocs Material свой favicon, поэтому у него ошибки нет.

**Проверка.** В отчёте Lighthouse провалены аудиты `is-on-https` и `errors-in-console` с URL
`http://se.ifmo.ru/o/favicon/`. Локально этого нет, потому что `localhost` отвечает 404 без
перенаправления.

**Решение.** `html_favicon` в Sphinx и `<link rel="icon">` в шаблоне Pelican. Итог: 100 баллов.
Ошибка показательна: она возникает только при размещении в подкаталоге чужого домена.

## 9. CI: «Resource not accessible by integration» на Configure Pages

**Ошибка.** Первые два запуска после push упали
([#1](https://github.com/andropovv/ssg-comparing-dz/actions/runs/37917139939),
[#2](https://github.com/andropovv/ssg-comparing-dz/actions/runs/37917473610)), скриншоты — в [CI/CD](ci.md#проваленный-запуск):

```text
HttpError: Resource not accessible by integration - https://docs.github.com/rest/pages/pages#get-a-apiname-pages-site
Get Pages site failed. Please verify that the repository has Pages enabled and configured to build using GitHub Actions
The strategy configuration was canceled because "build.pages" failed
```

**Гипотеза.** `actions/configure-pages` запрашивает настройки Pages через API, а Pages для
репозитория не включены. Сборка для Helios при этом исправна, её отменил `fail-fast` матрицы.

**Проверка.** В Settings → Pages стояло «Upgrade or make this repository public to enable Pages»:
репозиторий создан приватным, а на бесплатном тарифе Pages доступны только для публичных.
После смены видимости публичный API (`GET /repos/andropovv/ssg-comparing-dz`) вернул `"private": false, "has_pages": true`.

**Решение.** Перед публикацией вся история проверена на секреты (`git log -p --all`: ни пароля,
ни приватного ключа). Затем репозиторий сделан публичным, Source: GitHub Actions, добавлен секрет
`HELIOS_SSH_KEY`. После этого [запуск #3](https://github.com/andropovv/ssg-comparing-dz/actions/runs/37918009188)
прошёл полностью.

**Вывод для пайплайна.** Из-за `fail-fast: true` (значение по умолчанию) проблема одной площадки
останавливает и другую. Если Helios важнее, матрице стоит поставить `fail-fast: false`, а деплои
разнести по разным workflow.

## Прочие ошибки

| Ошибка | Причина | Решение |
|---|---|---|
| Pelican: LCP 6,2 с и Performance 52 на десктопе (у остальных 0,6–2,4 с) | 4,7 МБ `plotly.min.js` подключены в `<head>` без `defer` и блокируют отрисовку | `<script defer>`; благодаря обёртке из п. 1 график рисуется после загрузки. После исправления локально LCP 2,2 с и Performance 83, на Helios — 0,5 с и 94 |
| `rsync: --chmod=D755,F644: invalid argument` при ручном деплое с macOS | В macOS вместо rsync — openrsync без `--chmod` | Права ставит `build_all.sh` (`chmod 755/644`), `rsync -a` их сохраняет; в CI (Ubuntu, GNU rsync) `--chmod` оставлен как страховка |
| На мобильных скриншотах текст обрезан справа на всех трёх сайтах | `--window-size=390` в headless Chrome меняет окно, но не эмулирует устройство | Мобильные скриншоты через Playwright с профилем `Pixel 7` |
| Ссылки на страницы P2 из отчёта вели на `/p2/p2/mkdocs/` (404); `--strict` не сработал | Страница `p2.md` при `use_directory_urls: true` открывается как `/p2/`, и относительная ссылка считается от этого каталога. На ссылки вне `docs/` MkDocs выдаёт только `INFO … unrecognized relative link`, а не WARNING | Ссылки `mkdocs/`, `sphinx/`, `pelican/` относительно `/p2/`; урок — читать и INFO-сообщения сборки |
| Проверка нашла 404 на всех страницах P2 после сборки отчёта | `mkdocs build` с `--clean` очищает весь `site_dir`, включая `_build/site/p2/` | Порядок в `build_all.sh`: сначала отчёт, потом P2 |
| Проверка поискового индекса Sphinx не находит русское слово | `searchindex.js` хранит строки в виде `\uXXXX` и основы слов после стемминга | Разбирать JSON из `Search.setIndex(...)` и искать основу `затухан` |
| `check_site.py` на https: `URLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate` | Python с python.org на macOS не использует системное хранилище сертификатов (нужно запустить `Install Certificates.command`) | Явный `ssl.create_default_context(cafile=certifi.where())`; в CI (Ubuntu) ошибки не было бы |
| Lighthouse Performance одной страницы скачет 51 → 72 между запусками | Шум эмуляции CPU и сети | Медиана 3 прогонов, все значения приведены в таблице |
| Оценка ω в эксперименте завышена в 2–3 раза | Шум даёт ложные нули и пики сигнала | ω — по пику спектра (FFT с дополнением нулями), пики огибающей — по одному на период |
| `404.html` на Helios без стилей, если собрать с адресом GitHub Pages | `404.html` использует абсолютные пути из `site_url`: `/itmo-ssg/assets/...` вместо `/~s487249/ssg/assets/...` | Отдельная сборка под каждую площадку в матрице CI. Сам nginx на Helios всё равно отдаёт свою 404, а не нашу |
