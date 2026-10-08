"""Общие артефакты стресс-страницы P2: данные, статический и интерактивный графики.

Эксперимент: затухающие колебания x(t) = A·exp(-γt)·cos(ωt + φ).
Данные синтетические с фиксированным seed, поэтому сборка воспроизводима.
Результат кладётся в p2/shared/build/ и копируется каждым генератором.
"""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import plotly.offline  # noqa: E402

OUT = Path(__file__).parent / "build"
SEED = 42
SERIES = {  # серия: (A, γ, ω, φ, σ шума)
    "Серия 1": (1.0, 0.15, 2.0 * np.pi * 0.5, 0.0, 0.03),
    "Серия 2": (0.8, 0.30, 2.0 * np.pi * 0.5, 0.0, 0.03),
}


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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    t = np.linspace(0.0, 10.0, 401)
    data, results = {}, {}
    for name, (a, gamma, omega, phi, sigma) in SERIES.items():
        x = a * np.exp(-gamma * t) * np.cos(omega * t + phi) + rng.normal(0, sigma, t.size)
        data[name] = x
        g_fit, w_fit = fit_damped(t, x)
        results[name] = {"gamma_true": gamma, "gamma_fit": round(g_fit, 3),
                         "omega_true": round(omega, 3), "omega_fit": round(w_fit, 3)}

    with open(OUT / "data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t", *data])
        w.writerows(zip(t.round(4), *(v.round(5) for v in data.values())))
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Статический график (matplotlib)
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=120)
    for name, x in data.items():
        ax.plot(t, x, lw=1.2, label=name)
    ax.set_xlabel("t, с")
    ax.set_ylabel("x(t), отн. ед.")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "oscillation.png")
    plt.close(fig)

    # Фазовый портрет для двухколоночного блока
    fig, ax = plt.subplots(figsize=(3.6, 3.6), dpi=120)
    a, gamma, omega, phi, _ = SERIES["Серия 1"]
    x = a * np.exp(-gamma * t) * np.cos(omega * t + phi)  # модель без шума: производная от шума неинформативна
    ax.plot(x, np.gradient(x, t), lw=1.0)
    ax.set_xlabel("x")
    ax.set_ylabel("dx/dt")
    ax.set_title("Фазовый портрет, серия 1", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "phase.png")
    plt.close(fig)

    # Интерактивный график (Plotly): фрагмент без библиотеки + локальный plotly.min.js
    pfig = go.Figure([go.Scatter(x=t, y=x, mode="lines", name=n) for n, x in data.items()])
    pfig.update_layout(xaxis_title="t, с", yaxis_title="x(t)", height=360,
                       margin=dict(l=40, r=10, t=10, b=40), legend=dict(orientation="h"))
    fragment = pfig.to_html(full_html=False, include_plotlyjs=False, div_id="plotly-oscillation",
                            config={"responsive": True})
    # Генераторы подключают plotly.min.js в конце <body>, т.е. после inline-скрипта фрагмента.
    # Откладываем отрисовку до DOMContentLoaded, иначе "Plotly is not defined".
    fragment = fragment.replace("<script>", '<script>window.addEventListener("DOMContentLoaded", function () {', 1)
    fragment = fragment.replace("</script>", "});</script>", 1)
    (OUT / "plotly_fragment.html").write_text(fragment, encoding="utf-8")
    (OUT / "plotly.min.js").write_text(plotly.offline.get_plotlyjs(), encoding="utf-8")

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
