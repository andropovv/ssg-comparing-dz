"""Проверка развёрнутого сайта не «на глаз», а по признакам.

    python scripts/check_site.py https://se.ifmo.ru/~s487249/ssg/

1. HTTP 200 для отчёта и всех страниц P2.
2. Контрольная строка в HTML (защита от «200, но не та страница»: заглушка хостинга, старый кэш).
3. Поисковые индексы на месте и содержат русские слова из отчёта.
4. В HTML страниц P2 нет <script src>/<link href> на внешние хосты.
5. Формулы рендерятся при недоступных CDN: headless Chrome с правилом резолвера,
   которое «ломает» DNS для всех хостов, кроме проверяемого, затем ищем mjx-container в DOM.
"""

import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

PAGES = {
    "": "LAB1-SSG-REPORT-OK",
    "p2/mkdocs/": "P2-STRESS-PAGE-OK",
    "p2/sphinx/": "P2-STRESS-PAGE-OK",
    "p2/pelican/": "P2-STRESS-PAGE-OK",
}
SEARCH = {
    "search/search_index.json": "отладка",  # индекс lunr отчёта (MkDocs)
    "p2/mkdocs/search/search_index.json": "колебания",
    "p2/sphinx/searchindex.js": "затухан",  # Sphinx хранит основы слов (snowball-стеммер для ru)
}
CHROME_CANDIDATES = ["google-chrome", "chromium", "chromium-browser",
                     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]

failures: list[str] = []

try:
    # Python с python.org на macOS не видит системное хранилище сертификатов:
    # CERTIFICATE_VERIFY_FAILED на любом https. certifi есть в requirements.txt.
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()


def check(ok: bool, message: str) -> None:
    print(("OK   " if ok else "FAIL ") + message)
    if not ok:
        failures.append(message)


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "check-site/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CONTEXT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("src"):
            self.urls.append(a["src"])
        if tag == "link" and a.get("rel") in ("stylesheet", "preload", "modulepreload") and a.get("href"):
            self.urls.append(a["href"])


def find_chrome() -> str | None:
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for c in CHROME_CANDIDATES:
        if shutil.which(c) or os.path.exists(c):
            return shutil.which(c) or c
    return None


def math_rendered_offline(url: str, chrome: str) -> int:
    host = urlparse(url).hostname
    # Все хосты, кроме проверяемого, резолвятся в «не найдено» — имитация недоступных CDN.
    rules = f"MAP * ~NOTFOUND, EXCLUDE {host}"
    out = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                          f"--host-resolver-rules={rules}", "--virtual-time-budget=15000",
                          "--dump-dom", url],
                         capture_output=True, text=True, timeout=120).stdout
    return len(re.findall(r"<mjx-container", out))


def main() -> None:
    base = sys.argv[1].rstrip("/") + "/"
    host = urlparse(base).hostname
    print(f"Проверка {base}")

    for path, marker in PAGES.items():
        status, html = fetch(urljoin(base, path))
        check(status == 200, f"HTTP {status} /{path}")
        check(marker in html, f"контрольная строка {marker} на /{path}")
        if path.startswith("p2/"):
            parser = ResourceParser()
            parser.feed(html)
            external = [u for u in parser.urls if urlparse(urljoin(base + path, u)).hostname != host]
            check(not external, f"нет внешних script/link на /{path}" + (f": {external}" if external else ""))

    for path, word in SEARCH.items():
        status, body = fetch(urljoin(base, path))
        if status == 200 and path.endswith(".js"):  # Search.setIndex({...}) с \uXXXX-экранированием
            body = body[body.index("(") + 1:body.rindex(")")]
        if status == 200:
            body = json.dumps(json.loads(body), ensure_ascii=False)
        check(status == 200 and word in body.lower(), f"поисковый индекс /{path} содержит «{word}»")

    chrome = find_chrome()
    if chrome:
        for path in ("p2/mkdocs/", "p2/sphinx/", "p2/pelican/"):
            n = math_rendered_offline(urljoin(base, path), chrome)
            check(n >= 3, f"MathJax без внешней сети: {n} формул отрендерено на /{path}")
    else:
        print("SKIP проверка рендера формул: Chrome не найден")

    print(f"\nИтог: {'провалено ' + str(len(failures)) if failures else 'все проверки пройдены'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
