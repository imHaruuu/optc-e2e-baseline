import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = "figs"
os.makedirs(OUT, exist_ok=True)

GYRE = "/usr/share/texmf/fonts/opentype/public/tex-gyre/"
for f in ("texgyretermes-regular.otf", "texgyretermes-bold.otf", "texgyretermes-italic.otf"):
    if os.path.exists(GYRE + f):
        font_manager.fontManager.addfont(GYRE + f)

INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
C = {
    "eve": "#2a78d6",
    "kb": "#4a3aa7",
    "enum": "#eb6834",
    "json": "#eda100",
    "free": "#e87ba4",
    "ext": "#1baf7a",
    "big": "#008300",
    "rand": "#a3a29c",
    "bad": "#e34948",
}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["TeX Gyre Termes", "Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "axes.labelcolor": INK,
    "axes.edgecolor": INK2,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.8,
    "legend.frameon": False,
    "text.color": INK,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "pdf.fonttype": 42,
    "mathtext.fontset": "stix",
})

W = 7.0


def vn(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def pct(x, d=1):
    return f"{x * 100:.{d}f}".replace(".", ",") + "%"


def comma_axes(fig):
    fmt = FuncFormatter(lambda v, p: f"{v:g}".replace(".", ","))
    for ax in fig.axes:
        for axis, scale in ((ax.yaxis, ax.get_yscale()), (ax.xaxis, ax.get_xscale())):
            if scale == "linear" and isinstance(axis.get_major_formatter(), ScalarFormatter):
                axis.set_major_formatter(fmt)


def save(fig, name):
    comma_axes(fig)
    fig.savefig(f"{OUT}/{name}.pdf")
    fig.savefig(f"{OUT}/{name}.png", dpi=300)
    plt.close(fig)


def bar(ax, x, h, w, color, **kw):
    return ax.bar(x, h, w, color=color, edgecolor="white", linewidth=1.0, **kw)


def fig_arch():
    fig, ax = plt.subplots(figsize=(W, 2.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 33)
    ax.axis("off")

    def box(x, y, w, h, title, sub, edge, fill):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    linewidth=1.0, edgecolor=edge, facecolor=fill))
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center", fontsize=7.8, color=INK)
        if sub:
            ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=6.5, color=INK2)

    def arrow(p, q, style="-|>", ls="-"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=9, linewidth=1.0,
                                     color=INK2, linestyle=ls, shrinkA=1, shrinkB=1))

    kb_fill, kb_edge = "#efedf8", C["kb"]
    eve_fill, eve_edge = "#e9f1fb", C["eve"]
    io_fill, io_edge = "#f4f4f2", INK2
    y1, h = 18, 9
    box(1, y1, 14, h, "Cảnh báo $E$", "dãy sự kiện Sysmon", io_edge, io_fill)
    box(21, y1, 15, h, "Trích nhân chứng", "theo KB, tất định", kb_edge, kb_fill)
    box(40, y1, 13, h, "Tập ứng viên", r"$\mathcal{C}(E)$", kb_edge, kb_fill)
    box(59, y1, 18, h, "Xếp hạng bằng SLM", r"chỉ trong $\mathcal{C}(E)$", eve_edge, eve_fill)
    box(82, y1, 17, h, "Rút gọn tối thiểu", "+ kiểm tra entailment", kb_edge, kb_fill)
    y2 = 2.5
    box(38, y2, 17, h, "Không xác định", "", io_edge, io_fill)
    box(60, y2, 16, h, "Định tuyến", "giữ lại / leo thang", io_edge, io_fill)
    box(81, y2, 18, h, r"$(\hat t,\hat S)$, tập $\Gamma_\alpha$", "", io_edge, io_fill)
    yc = y1 + h / 2
    arrow((15.4, yc), (20.6, yc))
    arrow((36.4, yc), (39.6, yc))
    arrow((53.4, yc), (58.6, yc))
    arrow((77.4, yc), (81.6, yc))
    arrow((90.5, y1 - 0.4), (90.5, y2 + h + 0.4))
    arrow((46.5, y1 - 0.4), (46.5, y2 + h + 0.4))
    ax.text(47.5, 14.6, r"$\mathcal{C}=\emptyset$", ha="left", fontsize=7, color=INK2)
    arrow((80.6, y2 + h / 2), (76.4, y2 + h / 2))
    arrow((55.4, y2 + h / 2), (59.6, y2 + h / 2), ls="--")
    for x0, x1, lab, col in ((19.8, 54.2, "Quyền nói điều gì là có căn cứ", C["kb"]),
                             (57.8, 78.2, "Quyền chọn", C["eve"])):
        ax.add_patch(FancyBboxPatch((x0, y1 - 1.3), x1 - x0, h + 2.6, boxstyle="round,pad=0,rounding_size=1.5",
                                    linewidth=0.8, edgecolor=col, facecolor="none", linestyle=(0, (3, 2))))
        ax.text((x0 + x1) / 2, y1 + h + 2.4, lab, ha="center", fontsize=7.6, color=col)
    save(fig, "fig_arch")


def fig_rq1():
    sizes = ["0.5B", "1.5B", "7B"]
    data = [
        ("Sinh tự do", [0.004, 0.128, 0.105], C["free"]),
        ("JSON", [0.008, 0.117, 0.090], C["json"]),
        ("JSON-enum", [0.229, 0.026, 0.188], C["enum"]),
        ("EVE", [0.500, 0.496, 0.496], C["eve"]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.7), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axes[0]
    x = np.arange(3)
    w = 0.19
    for i, (name, v, col) in enumerate(data):
        xs = x + (i - 1.5) * w
        bar(ax, xs, v, w, col, label=name)
        for xi, vi in zip(xs, v):
            ax.text(xi, vi + 0.012, vn(vi, 3), ha="center", va="bottom", fontsize=5.6, color=INK2)
    ax.axhline(0.229, ls=(0, (4, 3)), lw=0.9, color=INK2)
    ax.text(-0.5, 0.237, "đa số 0,229", ha="left", fontsize=7, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Qwen2.5-{s}" for s in sizes])
    ax.set_ylabel("TTP top-1 (REAL, n = 266)")
    ax.set_ylim(0, 0.62)
    ax.set_title("(a) Độ chính xác kỹ thuật theo cỡ mô hình", loc="left")
    ax.legend(ncol=4, loc="upper left", columnspacing=0.9, handlelength=1.0, handletextpad=0.4)
    ax = axes[1]
    xs = [0.5, 1.5, 7.0]
    series = [
        ("Mã kỹ thuật hợp lệ", [0.100, 0.777, 0.962], INK2, "o", "-"),
        ("Bằng chứng bịa", [0.498, 0.083, 0.077], C["free"], "s", "-"),
        ("Kỹ thuật không căn cứ", [0.020, 0.773, 0.760], C["enum"], "^", "-"),
        ("Entailment (sinh tự do)", [0.000, 0.064, 0.031], C["rand"], "D", "-"),
        ("Entailment (EVE)", [1.0, 1.0, 1.0], C["eve"], "o", "--"),
    ]
    for name, v, col, m, ls in series:
        ax.plot(xs, v, marker=m, ms=5, lw=1.8, ls=ls, color=col, label=name,
                markeredgecolor="white", markeredgewidth=0.8)
    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels(["0,5B", "1,5B", "7B"])
    ax.minorticks_off()
    ax.set_ylim(-0.04, 1.1)
    ax.set_ylabel("Tỷ lệ")
    ax.set_xlabel("Số tham số (thang log)")
    ax.set_title("(b) Cỡ lớn sửa hình thức, không sửa căn cứ", loc="left")
    ax.legend(loc="center right", fontsize=7, bbox_to_anchor=(1.0, 0.45))
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig_rq1_scale")


def fig_rq2_choice():
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.7), gridspec_kw={"width_ratios": [0.8, 1.45]})
    ax = axes[0]
    k = ["0", "1", "2", "3"]
    n = [46, 197, 22, 1]
    cols = [C["rand"], C["kb"], C["eve"], C["eve"]]
    bar(ax, k, n, 0.65, cols)
    for i, v in enumerate(n):
        ax.text(i, v + 4, f"{v}\n({pct(v / 266)})", ha="center", va="bottom", fontsize=6.8, color=INK2)
    ax.set_ylim(0, 250)
    ax.set_xlabel(r"$|\mathcal{C}(E)|$ — số ứng viên KB đề xuất")
    ax.set_ylabel("Số cảnh báo (REAL, n = 266)")
    ax.set_title("(a) Mô hình chỉ được chọn ở 8,6% cảnh báo", loc="left")
    ax = axes[1]
    sets = ["REAL (n = 23)\nfirst: p = 0,15\nEVE: p = 0,15", "nontrivial (n = 118)\nfirst: p = 0,012\nEVE: p = 0,020", "attack_data (n = 245)\nfirst: p = 0,039\nEVE: p = 0,27"]
    rnd = np.array([0.319, 0.392, 0.138])
    lo = np.array([0.217, 0.322, 0.102])
    hi = np.array([0.391, 0.458, 0.171])
    first = [0.391, 0.475, 0.171]
    eve = [0.391, 0.466, 0.151]
    ceil = [0.435, 0.670, 0.310]
    x = np.arange(3)
    w = 0.25
    bar(ax, x - w, rnd, w, C["rand"], label="Ngẫu nhiên trong C(E)",
        yerr=[rnd - lo, hi - rnd], capsize=2.5, error_kw={"lw": 0.8, "ecolor": INK2})
    bar(ax, x, first, w, C["kb"], label="Luật first")
    bar(ax, x + w, eve, w, C["eve"], label="EVE 0,5B")
    for i in range(3):
        ax.plot([x[i] - 1.6 * w, x[i] + 1.6 * w], [ceil[i]] * 2, color=INK, lw=0.9, ls=(0, (1, 1.5)))
    ax.plot([], [], color=INK, lw=0.9, ls=(0, (1, 1.5)), label="Trần: gold $\\in$ C(E)")
    ax.set_xticks(x)
    ax.set_xticklabels(sets, fontsize=7)
    ax.set_ylim(0, 0.92)
    ax.set_ylabel(r"TTP top-1 trên cảnh báo có $|\mathcal{C}|\geq 2$")
    ax.set_title("(b) Khi phải chọn, SLM không vượt luật first", loc="left")
    ax.legend(ncol=2, loc="upper left", columnspacing=1.0, handlelength=1.2)
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig_rq2_choice")


def fig_rq2_kb_transfer():
    tech = ["T1003", "T1036", "T1047", "T1055", "T1059", "T1218", "T1490", "T1543", "T1553", "T1574"]
    ad1 = [0.288, 0.025, 0.12, 0.822, 0.799, 0.858, 0.985, 0.929, 0.0, 0.570]
    ad2 = [0.288, 0.393, 0.82, 0.822, 0.799, 0.858, 0.985, 0.929, 0.540, 0.570]
    at1 = [0.119, 0.200, 0.067, 0.233, 0.700, 0.250, 0.293, 0.286, 0.0, 0.209]
    at2 = [0.119, 0.133, 0.050, 0.233, 0.700, 0.250, 0.293, 0.286, 0.087, 0.209]
    fig, ax = plt.subplots(figsize=(W, 2.9))
    y = np.arange(len(tech))
    off = 0.17
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.grid(axis="y", visible=False)
    for yi, a, b in zip(y, ad1, ad2):
        if abs(b - a) > 1e-6:
            ax.annotate("", xy=(b, yi - off), xytext=(a, yi - off),
                        arrowprops=dict(arrowstyle="-|>", color=C["eve"], lw=1.2, shrinkA=3, shrinkB=3))
    for yi, a, b in zip(y, at1, at2):
        if abs(b - a) > 1e-6:
            ax.annotate("", xy=(b, yi + off), xytext=(a, yi + off),
                        arrowprops=dict(arrowstyle="-|>", color=C["enum"], lw=1.2, shrinkA=3, shrinkB=3))
    kw = dict(s=26, zorder=3, linewidths=1.2)
    ax.scatter(ad1, y - off, facecolors="white", edgecolors=C["eve"], label="AD-GEN, KB v0.1", **kw)
    ax.scatter(ad2, y - off, color=C["eve"], edgecolors="white", label="AD-GEN, KB v0.2", **kw)
    ax.scatter(at1, y + off, facecolors="white", edgecolors=C["enum"], label="attack_data, KB v0.1", **kw)
    ax.scatter(at2, y + off, color=C["enum"], edgecolors="white", label="attack_data, KB v0.2", **kw)
    ax.set_yticks(y)
    ax.set_yticklabels(tech)
    ax.invert_yaxis()
    ax.set_xlim(-0.03, 1.03)
    ax.set_xlabel("Độ phủ của C(E) theo kỹ thuật (gold $\\in$ C(E))")
    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), columnspacing=1.2)
    fig.tight_layout()
    save(fig, "fig_rq2_kb_transfer")


def fig_cost():
    pts = [
        ("kb_only", 0.3, 0.500, 0.444, 0.564, C["kb"], "s", True, (0.42, 0.575, "left")),
        ("Extractive TF-IDF", 5.9, 0.289, 0.233, 0.350, C["ext"], "s", False, (8.0, 0.300, "left")),
        ("EVE 0,5B", 1500, 0.500, 0.444, 0.564, C["eve"], "o", False, (1500, 0.590, "center")),
        ("JSON-enum 0,5B", 3589, 0.229, 0.180, 0.278, C["enum"], "o", False, (2500, 0.145, "center")),
        ("EVE 1,5B", 4511, 0.496, 0.440, 0.556, C["eve"], "^", False, (4511, 0.405, "center")),
        ("EVE 7B", 18749, 0.496, 0.440, 0.556, C["eve"], "D", False, (18749, 0.590, "center")),
        ("JSON-enum 7B", 38710, 0.188, 0.143, 0.237, C["enum"], "D", False, (38710, 0.105, "center")),
    ]
    fig, ax = plt.subplots(figsize=(W, 2.9))
    ax.grid(axis="x", which="major", color=GRID, lw=0.6)
    ax.axhline(0.229, ls=(0, (4, 3)), lw=0.8, color=INK2)
    ax.text(0.2, 0.237, "đa số 0,229", fontsize=7, color=INK2)
    ax.axhline(0.500, ls=(0, (1, 1.5)), lw=0.9, color=C["kb"])
    ax.text(90, 0.514, "frontier Pareto: chỉ kb_only", fontsize=7, color=C["kb"], style="italic")
    for name, lat, acc, lo, hi, col, m, par, (tx, ty, ha) in pts:
        ax.errorbar(lat, acc, yerr=[[acc - lo], [hi - acc]], fmt=m, color=col, ms=7 if par else 6,
                    mec=INK if par else "white", mew=1.4 if par else 0.8, capsize=2.5, elinewidth=0.9)
        ax.text(tx, ty, name, fontsize=7.4, ha=ha, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(0.15, 1.3e5)
    ax.set_ylim(0.06, 0.65)
    ax.set_xlabel("Độ trễ trung bình mỗi cảnh báo trên CPU (ms, thang log) — Ryzen 9 9950X, fp32, 16 luồng")
    ax.set_ylabel("TTP top-1 (REAL, n = 266)")
    fig.tight_layout()
    save(fig, "fig_cost_pareto")


def fig_rq3_route():
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.6), gridspec_kw={"width_ratios": [1, 1.1]})
    ax = axes[0]
    w = 0.32
    bar(ax, [0 - w / 2], [0.629], w, C["eve"], label="Trả lời bởi 0,5B")
    bar(ax, [1 - w / 2], [0.018], w, C["eve"])
    bar(ax, [1 + w / 2], [0.0], w, C["big"], label="Trả lời bởi 7B")
    for xi, v in ((0 - w / 2, 0.629), (1 - w / 2, 0.018), (1 + w / 2, 0.0)):
        ax.text(xi, v + 0.015, vn(v), ha="center", fontsize=7, color=INK2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Giữ lại\n(|Γ| = 1, n = 210)", "Leo thang\n(n = 56)"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("TTP top-1")
    ax.set_title("(a) Tách nhóm tốt, nhưng 7B không cứu được", loc="left")
    ax.legend(loc="upper right")
    ax = axes[1]
    names = ["Chỉ 0,5B", "Định tuyến\nambiguous", "Định tuyến\nnot_singleton", "Chỉ 7B"]
    lat = [1500, 1800, 13736, 18749]
    acc = [0.500, 0.496, 0.496, 0.496]
    cols = [C["eve"], C["eve"], C["eve"], C["big"]]
    alphas = [1.0, 0.75, 0.5, 1.0]
    for i, (l, c, a) in enumerate(zip(lat, cols, alphas)):
        ax.bar(i, l, 0.62, color=c, alpha=a, edgecolor="white", linewidth=1.0)
        ax.text(i, l + 450, f"{l:,} ms".replace(",", " ") + f"\nacc {vn(acc[i])}", ha="center", fontsize=6.8, color=INK2)
    ax.set_xticks(range(4))
    ax.set_xticklabels(names, fontsize=7.4)
    ax.set_ylim(0, 23500)
    ax.set_ylabel("ms mỗi cảnh báo trên CPU")
    ax.set_title("(b) Chi phí tăng ~9 lần, độ chính xác không đổi", loc="left")
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig_rq3_route")


def fig_rq4():
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.8), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    cats = ["instruction", "claim_technique", "attested_instr."]
    n = np.array([563, 563, 886])
    eve_ok = np.array([0, 6, 96]) / n
    je_ok = np.array([0, 0, 25]) / n
    je_bad = np.array([87, 393, 205]) / n
    x = np.arange(3)
    w = 0.34
    bar(ax, x - w / 2, eve_ok, w, C["eve"], label="EVE: đổi vì bằng chứng đổi")
    bar(ax, x + w / 2, je_ok, w, C["json"], label="JSON-enum: đổi vì bằng chứng đổi")
    ax.bar(x + w / 2, je_bad, w, bottom=je_ok, color=C["bad"], edgecolor="white", linewidth=1.0,
           hatch="////", label="Đổi khi bằng chứng giữ nguyên")
    for i in range(3):
        ax.text(x[i] - w / 2, eve_ok[i] + 0.015, pct(eve_ok[i]), ha="center", fontsize=6.8, color=INK2)
        ax.text(x[i] + w / 2, je_ok[i] + je_bad[i] + 0.015, pct(je_ok[i] + je_bad[i]), ha="center", fontsize=6.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylim(0, 0.95)
    ax.set_ylabel("Tỷ lệ cảnh báo đổi kỹ thuật")
    ax.set_title("(a) Kênh kỹ thuật", loc="left")
    ax.legend(loc="upper left", fontsize=7)
    ax = axes[1]
    pay = ["instruction", "attested_instr.", "attested_rename"]
    slm = [0.737, 1.0, 0.142]
    kbv = [0.0, 0.052, 0.641]
    x = np.arange(3)
    w = 0.34
    bar(ax, x - w / 2, slm, w, C["free"], label="Verdict SLM: độc hại → lành tính")
    bar(ax, x + w / 2, kbv, w, C["kb"], label="Verdict thuần luật: tỷ lệ lật")
    for i in range(3):
        ax.text(x[i] - w / 2, slm[i] + 0.02, pct(slm[i], 0), ha="center", fontsize=6.8, color=INK2)
        ax.text(x[i] + w / 2, kbv[i] + 0.02, pct(kbv[i], 0), ha="center", fontsize=6.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(pay)
    ax.set_ylim(0, 1.45)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_title("(b) Kênh verdict", loc="left")
    ax.legend(loc="upper left", fontsize=7)
    fig.tight_layout(w_pad=1.6)
    save(fig, "fig_rq4_injection")


if __name__ == "__main__":
    fig_arch()
    fig_rq1()
    fig_rq2_choice()
    fig_rq2_kb_transfer()
    fig_cost()
    fig_rq3_route()
    fig_rq4()
    print("Done:", sorted(os.listdir(OUT)))
