| Генератор | Режим | Performance (медиана; прогоны) | Accessibility | Best Practices | SEO | Вес страницы, КБ | Запросов | Внешних запросов | LCP, мс |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MkDocs Material | mobile | 53 (53, 50, 53) | 86 | 100 | 92 | 7184 | 17 | 0 | 13845 |
| MkDocs Material | desktop | 84 (84, 84, 84) | 86 | 100 | 92 | 7184 | 15 | 0 | 2409 |
| Sphinx + MyST | mobile | 71 (71, 71, 71) | 94 | 100 | 91 | 7063 | 17 | 0 | 2855 |
| Sphinx + MyST | desktop | 92 (92, 92, 91) | 91 | 100 | 91 | 7063 | 17 | 0 | 604 |
| Pelican | mobile | 54 (54, 54, 56) | 93 | 100 | 91 | 6935 | 12 | 0 | 37493 |
| Pelican | desktop | 83 (83, 83, 83) | 93 | 100 | 91 | 6935 | 12 | 0 | 2154 |

Адрес: `http://localhost:8765`. Lighthouse 12.8.2, mobile — эмуляция Moto G Power с замедлением сети и CPU, desktop — `--preset=desktop`.
