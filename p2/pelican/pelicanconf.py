"""Pelican: та же стресс-страница P2."""

AUTHOR = "s487249"
SITENAME = "P2 · Pelican"
SITEURL = ""
TIMEZONE = "Europe/Moscow"
DEFAULT_LANG = "ru"

PATH = "content"
OUTPUT_PATH = "../../_build/site/p2/pelican"
STATIC_PATHS = ["assets"]
# Иначе Pelican считает любой .html в content/ исходником статьи и требует метаданные title.
READERS = {"html": None}
# Относительные ссылки: сайт работает и в корне, и в подкаталоге (/~s487249/ssg/p2/pelican/).
RELATIVE_URLS = True

# Pelican — блоговый движок: отключаем ленту, архивы и т.п., оставляем одну страницу.
DIRECT_TEMPLATES = []
FEED_ALL_ATOM = FEED_ALL_RSS = CATEGORY_FEED_ATOM = TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = AUTHOR_FEED_RSS = None
AUTHOR_SAVE_AS = CATEGORY_SAVE_AS = TAG_SAVE_AS = ""
DISPLAY_PAGES_ON_MENU = False
LINKS = SOCIAL = ()

THEME = "notmyidea"
# Частичное переопределение темы без форка: шаблоны из templates/ имеют приоритет,
# а исходный шаблон доступен как "!theme/page.html".
THEME_TEMPLATES_OVERRIDES = ["templates"]

PLUGIN_PATHS = ["plugins"]
PLUGINS = ["bibcite"]
BIBCITE_FILE = "../shared/refs.bib"

MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {"css_class": "highlight", "linenums": True},
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
        "markdown.extensions.toc": {},
        "pymdownx.arithmatex": {"generic": True},
        "pymdownx.snippets": {"base_path": ["../shared/build"], "check_paths": True},
    },
    "output_format": "html5",
}
