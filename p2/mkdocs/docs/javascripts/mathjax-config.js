// Конфигурация MathJax должна быть задана до загрузки tex-svg.js.
// tags: 'ams' включает нумерацию окружений equation и работу \label/\eqref.
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
    tags: "ams"
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};
