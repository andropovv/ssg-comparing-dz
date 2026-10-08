| Генератор | Режим | Performance | Accessibility | Best Practices | SEO | Вес страницы, КБ | Запросов | Внешних запросов | LCP, мс |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MkDocs Material | mobile | 36 | 86 | 100 | 92 | 7405 | 26 | 9 | 40280 |
| MkDocs Material | desktop | 69 | 86 | 100 | 92 | 7405 | 24 | 9 | 6589 |
| Sphinx + MyST | mobile | 51 | 94 | 96 | 91 | 7063 | 17 | 0 | 27162 |
| Sphinx + MyST | desktop | 69 | 91 | 96 | 91 | 7063 | 17 | 0 | 4559 |
| Pelican | mobile | 36 | 93 | 96 | 91 | 6934 | 12 | 0 | 37973 |
| Pelican | desktop | 52 | 93 | 96 | 91 | 6934 | 12 | 0 | 6235 |

Адрес: `http://localhost:8765`. Lighthouse 12.8.2, mobile — эмуляция Moto G Power с замедлением сети и CPU, desktop — `--preset=desktop`.
