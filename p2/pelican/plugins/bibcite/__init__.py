"""Минимальная поддержка BibTeX для Pelican.

У Pelican нет поддерживаемого плагина цитирования, поэтому реализуем сами:
[@key] в тексте → «[n]» со ссылкой, абзац [bibliography] → нумерованный список
в стиле unsrt (pybtex). Нумерация — в порядке первого упоминания.
"""

import re
from pathlib import Path

from pelican import signals
from pybtex.database import parse_file
from pybtex.plugin import find_plugin

CITE = re.compile(r"\[@([\w:-]+)\]")
BIB_MARK = "<p>[bibliography]</p>"


def _render(instance):
    content = instance._content
    if not content or "[@" not in content:
        return
    bib_path = Path(instance.settings["PATH"]).parent / instance.settings["BIBCITE_FILE"]
    bib = parse_file(str(bib_path), bib_format="bibtex")

    order: list[str] = []
    for key in CITE.findall(content):
        if key not in order:
            order.append(key)

    def cite(match):
        n = order.index(match.group(1)) + 1
        return f'<a class="citation" href="#bib-{match.group(1)}">[{n}]</a>'

    content = CITE.sub(cite, content)

    style = find_plugin("pybtex.style.formatting", "unsrt")()
    backend = find_plugin("pybtex.backends", "html")()
    # Список, а не генератор: pybtex обходит записи дважды (метки, затем текст),
    # и с генератором в библиографию попадает только одна запись.
    formatted = style.format_entries([bib.entries[k] for k in order])
    items = "\n".join(
        f'<li id="bib-{entry.key}">{entry.text.render(backend)}</li>' for entry in formatted
    )
    instance._content = content.replace(BIB_MARK, f'<ol class="bibliography">\n{items}\n</ol>')


def register():
    signals.content_object_init.connect(_render)
