"""Sphinx + MyST: та же стресс-страница P2."""

project = "P2 · Sphinx + MyST"
author = "s487249"
language = "ru"

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinxcontrib.bibtex",
]
myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence", "attrs_block"]
myst_heading_anchors = 2

root_doc = "index"
exclude_patterns = ["_build"]

# Нумерация рисунков, таблиц и листингов; для language="ru" подписи «Рис. N», «Таблица N».
numfig = True
math_numfig = True

bibtex_bibfiles = ["../shared/refs.bib"]
bibtex_default_style = "unsrt"
bibtex_reference_style = "label"

html_theme = "furo"
html_title = project
html_static_path = ["../shared/build", "../shared/vendor"]
html_js_files = ["plotly.min.js"]
# Без favicon браузер запрашивает /favicon.ico в корне se.ifmo.ru, а тот редиректит на http:// —
# mixed content, ошибка в консоли и −25 баллов Best Practices в Lighthouse.
html_favicon = "../shared/vendor/favicon.png"
# MathJax берётся из _static, а не с CDN: формулы работают при недоступности внешних сетей.
mathjax_path = "tex-svg.js"
# Без точки и пробела в формате Furo склеивает номер с подписью: «Список 1make_figures.py».
numfig_format = {"figure": "Рис. %s.", "table": "Таблица %s.", "code-block": "Листинг %s."}
