# Затухающие колебания: стресс-тест научного контента

Контрольная строка: `P2-STRESS-PAGE-OK`.

## Введение {#intro}

Затухающие колебания — классическая модель линейной системы с трением [@landau1988].
Обработка данных выполнена на NumPy [@harris2020], графики построены в Matplotlib [@hunter2007].
Данные синтетические, сгенерированы с фиксированным зерном генератора[^seed].

[^seed]: `numpy.random.default_rng(42)`, поэтому сборка страницы воспроизводима.

## Модель {#model}

Смещение осциллятора описывается выражением

\begin{equation}
x(t) = A\,e^{-\gamma t}\cos(\omega t + \varphi),
\label{eq:oscillator}
\end{equation}

где $\gamma$ — коэффициент затухания, $\omega$ — циклическая частота.
Логарифм огибающей из $\eqref{eq:oscillator}$ линеен по $t$: $\ln|x_{\max}(t)| = \ln A - \gamma t$.
Именно это свойство используется в разделе [«Методика»](#method).

## Методика {#method}

<div class="grid" markdown>

<div markdown>
Частота $\omega$ оценивается по положению пика спектра сигнала, дополненного нулями.
Затем сигнал разбивается на окна длиной в один период, в каждом окне берётся максимум,
и по этим точкам методом наименьших квадратов подбирается прямая $\ln x = \ln A - \gamma t$.
Фазовый портрет справа показывает скручивающуюся к нулю спираль — признак затухания.
</div>

<div markdown>
![Фазовый портрет серии 1](assets/phase.png){ loading=lazy }
</div>

</div>

Реализация алгоритма:

```python linenums="1" title="make_figures.py"
def fit_damped(t: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    """Оценка ω по пику спектра и γ по огибающей из максимумов на каждом периоде."""
    dt = t[1] - t[0]
    n = 16 * t.size  # дополнение нулями уточняет положение пика спектра
    freqs = np.fft.rfftfreq(n, dt)
    omega = 2.0 * np.pi * freqs[np.argmax(np.abs(np.fft.rfft(x, n)))]
    step = int(round(2.0 * np.pi / omega / dt))
    peaks = [i + int(np.argmax(x[i:i + step])) for i in range(0, t.size - step, step)]
    slope, _ = np.polyfit(t[peaks], np.log(x[peaks]), 1)
    return -slope, omega
```

## Результаты {#results}

/// table-caption
Заданные и оценённые параметры модели $\eqref{eq:oscillator}$
///

<table>
  <thead>
    <tr><th rowspan="2">Серия</th><th colspan="2">γ, с⁻¹</th><th colspan="2">ω, рад/с</th></tr>
    <tr><th>задано</th><th>оценка</th><th>задано</th><th>оценка</th></tr>
  </thead>
  <tbody>
    <tr><td>Серия 1</td><td>0,150</td><td>0,134</td><td>3,142</td><td>3,173</td></tr>
    <tr><td>Серия 2</td><td>0,300</td><td>0,244</td><td>3,142</td><td>3,173</td></tr>
    <tr><td colspan="5">Условия: σ шума = 0,03; N = 401 точка; t ∈ [0; 10] с</td></tr>
  </tbody>
</table>

Оценки получены алгоритмом из раздела [«Методика»](#method).

![Сигнал двух серий](assets/oscillation.png)

/// figure-caption
Статический график (Matplotlib): смещение $x(t)$ для двух серий
///

Интерактивная версия того же графика (Plotly, библиотека загружается локально):

--8<-- "assets/plotly_fragment.html"

## Литература

\bibliography
