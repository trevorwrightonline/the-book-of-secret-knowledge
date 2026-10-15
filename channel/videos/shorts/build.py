"""Six Shorts (1080x1920) cut from the three long-form videos, with burned-in captions.

Run from channel/:  python3 videos/shorts/build.py [name ...]
"""
import os, sys, re, importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(CH, "lib"))
from engine import Scene, render, txt, box, C, money, ease  # noqa
from words import dollars, words  # noqa

OUT = os.path.join(CH, "out", "shorts")
os.makedirs(OUT, exist_ok=True)


def load(name):
    p = os.path.join(CH, "videos", name, "build.py")
    sys.path.insert(0, os.path.dirname(p))
    sys.modules.pop("model", None)  # each video has its own model.py
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V3, V1, V2 = load("v03_real_cost"), load("v01_rent_vs_buy"), load("v02_down_payment")


def chunks(text, maxc=20):
    out, cur = [], ""
    for w in text.split():
        if cur and (len(cur) + 1 + len(w) > maxc or cur[-1] in ".?!"):
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return out + ([cur] if cur else [])


def captions(scenes):
    def overlay(fig, c, si):
        text = getattr(scenes[si], "caps", scenes[si].beats)[c.beat]
        parts = chunks(text)
        weights = np.cumsum([len(p) + 2 for p in parts])
        speech = max(0.1, c.beat_d - 0.3)
        k = int(np.searchsorted(weights / weights[-1], min(0.999, c.beat_t / speech), side="right"))
        txt(fig, 0.5, 0.2, parts[min(k, len(parts) - 1)].upper(), size=56, color=C["text"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#000000", edgecolor="none", alpha=0.55))
        txt(fig, 0.5, 0.05, "@the30secondagent", size=22, weight="medium", color=C["muted"])
    return overlay


def title(fig, s, color=None):
    txt(fig, 0.5, 0.9, s, size=56, color=color or C["text"])


def prog(c, frac=0.9):
    return min(1.0, c.beat_t / max(0.1, c.beat_d * frac))


# ---------- 1. Year 1 of your mortgage ----------
def s1_draw(fig, c):
    y1 = V3.Y_INT[0] + V3.Y_PRIN[0]
    title(fig, "YEAR 1 OF A MORTGAGE")
    txt(fig, 0.5, 0.82, f"$400k home · 20% down · {V3.RATE:.2f}%", size=34, weight="medium", color=C["muted"])
    txt(fig, 0.5, 0.68, money(y1 * (c.bp if c.beat == 0 else 1)), size=110)
    txt(fig, 0.5, 0.62, "paid in year 1", size=34, weight="medium", color=C["muted"])
    if c.beat >= 1:
        fp = V3.Y_PRIN[0] / y1
        p = c.bp if c.beat == 1 else 1
        box(fig, 0.08, 0.45, 0.84 * fp, 0.08, C["green"])
        box(fig, 0.08 + 0.84 * fp, 0.45, 0.84 * (1 - fp) * p, 0.08, C["red"])
        txt(fig, 0.08, 0.41, f"House: {money(V3.Y_PRIN[0])}", size=36, color=C["green"], ha="left")
        txt(fig, 0.92, 0.41, f"Bank: {money(V3.Y_INT[0])}", size=36, color=C["red"], ha="right", alpha=p)
    if c.beat >= 2:
        txt(fig, 0.5, 0.31, f"{V3.Y_INT[0] / y1:.0%} goes to interest", size=60, color=C["amber"], alpha=c.bp)


S1 = [Scene(draw=s1_draw, beats=[
    f"You buy a four hundred thousand dollar house. In year one, you pay about {dollars(V3.Y_INT[0] + V3.Y_PRIN[0])} "
    "on the mortgage.",
    f"But only {dollars(V3.Y_PRIN[0])} of that actually goes to the house. The bank keeps {dollars(V3.Y_INT[0])}.",
    f"That's {words(round(100 * V3.Y_INT[0] / (V3.Y_INT[0] + V3.Y_PRIN[0])))} percent interest. The full thirty-year "
    "breakdown is in the linked video.",
])]


# ---------- 2. Same house, two states ----------
def s2_draw(fig, c):
    title(fig, "SAME $400K HOUSE")
    txt(fig, 0.5, 0.84, "Property tax over 30 years", size=38, weight="medium", color=C["muted"])
    data = [("HAWAII", V3.TAX_HI, C["green"]), ("ILLINOIS", V3.TAX_IL, C["red"])]
    for i, (n, r, cc) in enumerate(data[: c.beat + 1]):
        y = 0.68 - i * 0.2
        p = c.bp if i == c.beat else 1
        v = r * V3.PRICE * 30
        txt(fig, 0.5, y + 0.04, n, size=50, alpha=p)
        txt(fig, 0.5, y - 0.04, money(v * p), size=100, color=cc)
    if c.beat >= 2:
        txt(fig, 0.5, 0.34, f"{money((V3.TAX_IL - V3.TAX_HI) * V3.PRICE * 30)} difference", size=58,
            color=C["amber"], alpha=c.bp)


S2 = [Scene(draw=s2_draw, beats=[
    f"Same four hundred thousand dollar house. In Hawaii, thirty years of property tax is about "
    f"{dollars(V3.TAX_HI * V3.PRICE * 30)}.",
    f"In Illinois, it's about {dollars(V3.TAX_IL * V3.PRICE * 30)}.",
    f"That's a {dollars((V3.TAX_IL - V3.TAX_HI) * V3.PRICE * 30)} difference, for the exact same house. "
    "Here's the real cost of a house, line by line.",
])]


# ---------- 3. Rent vs buy race ----------
def s3_draw(fig, c):
    H = V1.H
    title(fig, "RENT vs BUY · 1996 → 2025")
    txt(fig, 0.5, 0.85, "Net worth, real US data", size=36, weight="medium", color=C["muted"])
    ax = fig.add_axes([0.1, 0.35, 0.82, 0.45])
    p = prog(c) if c.beat == 1 else (0.02 if c.beat == 0 else 1)
    k = max(2, int(len(H) * p))
    ax.plot(H.index[:k], H.buyer.iloc[:k], color=C["red"], lw=6, label="Bought")
    ax.plot(H.index[:k], H.renter.iloc[:k], color=C["teal"], lw=6, label="Rented + invested")
    ax.set_xlim(H.index[0], H.index[-1]); ax.set_ylim(0, H.renter.max() * 1.12)
    for s in ax.spines.values(): s.set_visible(False)
    ax.grid(axis="y", color=C["grid"]); ax.tick_params(labelsize=22)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:,.0f}k")
    ax.legend(loc="upper left", frameon=False, fontsize=28, labelcolor=C["text"])
    if c.beat >= 2:
        txt(fig, 0.5, 0.3, f"Renter {money(V1.R['renter'])}  ·  Buyer {money(V1.R['buyer'])}", size=36, alpha=c.bp)


S3 = [Scene(draw=s3_draw, live=True, beats=[
    "Is renting really throwing money away? I ran thirty years of real data.",
    "One person buys a median home in nineteen ninety-six. The other rents a similar place, and invests every dollar "
    "they save.",
    f"Thirty years later, the renter has about {dollars(V1.R['renter'])}. The buyer, about {dollars(V1.R['buyer'])}. "
    "But one number can flip the result. Full test in the linked video.",
])]


# ---------- 4. Both throw money away ----------
def s4_draw(fig, c):
    title(fig, "MONEY GONE FOR GOOD")
    txt(fig, 0.5, 0.84, "30 years · real US data", size=36, weight="medium", color=C["muted"])
    txt(fig, 0.5, 0.7, "RENTER", size=50, color=C["teal"])
    txt(fig, 0.5, 0.63, money(V1.RENT_GONE * (c.bp if c.beat == 0 else 1)), size=96)
    txt(fig, 0.5, 0.585, "rent", size=30, weight="medium", color=C["muted"])
    if c.beat >= 1:
        p = c.bp if c.beat == 1 else 1
        txt(fig, 0.5, 0.48, "BUYER", size=50, color=C["red"], alpha=p)
        txt(fig, 0.5, 0.41, money(V1.BUYER_GONE * p), size=96)
        txt(fig, 0.5, 0.365, "interest, tax, insurance, upkeep, fees", size=30, weight="medium", color=C["muted"], alpha=p)
    if c.beat >= 2:
        txt(fig, 0.5, 0.29, "Both “throw money away”", size=56, color=C["amber"], alpha=c.bp)


S4 = [Scene(draw=s4_draw, beats=[
    f"Renters throw money away? Over thirty years, our renter paid about {dollars(V1.RENT_GONE)} in rent.",
    f"But the buyer also paid about {dollars(V1.BUYER_GONE)} they'll never get back. Interest, property tax, "
    "insurance, maintenance, and fees.",
    "Both threw money away. The real question is who built more on the side. Watch the full test.",
])]


# ---------- 5 & 6. Fastest / slowest cities ----------
def city_short(sub, head, color):
    sub = sub.reset_index(drop=True)

    def d(fig, c):
        title(fig, head, color)
        txt(fig, 0.5, 0.84, "Years to save a 20% down payment", size=36, weight="medium", color=C["muted"])
        shown = 0 if c.beat == 0 else min(len(sub), int(prog(c) * len(sub)) + 1)
        for i in range(shown):
            r = sub.iloc[i]
            y = 0.74 - i * 0.09
            nm = r.city.replace("New York (Brooklyn)", "Brooklyn")
            txt(fig, 0.08, y, f"#{int(r['rank'])} {nm}", size=46, ha="left")
            txt(fig, 0.92, y, f"{r.years:.1f} yrs", size=50, color=color, ha="right")
    return d


fast = V2.DF.head(5).iloc[::-1]
slow = V2.DF.tail(5)


def list_beat(sub):
    return " ".join(f"{V2.say(r.city)}, {V2.yw(r.years)}." for _, r in sub.iterrows())


S5 = [Scene(draw=city_short(fast, "FASTEST CITIES", C["green"]), live=True, beats=[
    "The five big US cities where you can save a house down payment the fastest.",
    list_beat(fast) + " Where does your city rank? All fifty are in the linked video.",
])]
S6 = [Scene(draw=city_short(slow, "SLOWEST CITIES", C["red"]), live=True, beats=[
    "The five big US cities where saving a house down payment takes the longest.",
    list_beat(slow) + " See where your city ranks. All fifty are in the linked video.",
])]

y1 = V3.Y_INT[0] + V3.Y_PRIN[0]
S1[0].caps = [f"You buy a $400,000 house. Year one, you pay {money(y1)} on the mortgage.",
              f"Only {money(V3.Y_PRIN[0])} goes to the house. The bank keeps {money(V3.Y_INT[0])}.",
              f"That's {V3.Y_INT[0] / y1:.0%} interest. Full 30-year breakdown in the linked video."]
S2[0].caps = [f"Same $400,000 house. Hawaii: {money(V3.TAX_HI * V3.PRICE * 30)} in property tax over 30 years.",
              f"Illinois: {money(V3.TAX_IL * V3.PRICE * 30)}.",
              f"A {money((V3.TAX_IL - V3.TAX_HI) * V3.PRICE * 30)} difference for the same house."]
S3[0].caps = ["Is renting throwing money away? I ran 30 years of real data.",
              "One buys a median home in 1996. One rents and invests every dollar saved.",
              f"Renter: {money(V1.R['renter'])}. Buyer: {money(V1.R['buyer'])}. One number can flip it."]
S4[0].caps = [f"Renters throw money away? Ours paid {money(V1.RENT_GONE)} in rent.",
              f"The buyer paid {money(V1.BUYER_GONE)} they'll never get back.",
              "Both threw money away. Who built more on the side?"]
S5[0].caps = ["5 big US cities where you save a down payment fastest",
              " ".join(f"{r.city}: {r.years:.1f} years." for _, r in fast.iterrows()) + " All 50 in the linked video."]
S6[0].caps = ["5 big US cities where saving a down payment takes longest",
              " ".join(f"{r.city.replace('New York (Brooklyn)', 'Brooklyn')}: {r.years:.1f} years." for _, r in slow.iterrows())
              + " All 50 in the linked video."]

SHORTS = {
    "s1_year1_mortgage": (S1, "Year 1 of a mortgage: where your money goes #shorts", "v03"),
    "s2_property_tax_states": (S2, "Same $400K house, $178K difference in taxes #shorts", "v03"),
    "s3_rent_vs_buy_race": (S3, "Rent vs buy: 30 years of real data #shorts", "v01"),
    "s4_both_throw_money": (S4, "Renting is throwing money away? So is buying. #shorts", "v01"),
    "s5_fastest_cities": (S5, "Fastest US cities to save a down payment #shorts", "v02"),
    "s6_slowest_cities": (S6, "Slowest US cities to save a down payment #shorts", "v02"),
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(SHORTS)
    with open(os.path.join(OUT, "titles.txt"), "w") as f:
        for n, (sc, t, rel) in SHORTS.items():
            f.write(f"{n}.mp4\n  Title: {t}\n  Related video: {rel}\n\n")
    for n in names:
        sc = SHORTS[n][0]
        total, _ = render(sc, os.path.join(OUT, f"{n}.mp4"), W=1080, H=1920, overlay=captions(sc))
        print(n, f"{total:.1f}s")
