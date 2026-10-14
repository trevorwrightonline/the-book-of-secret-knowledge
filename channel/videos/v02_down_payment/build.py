"""Video 2: How Long It Takes to Save a Down Payment in 50 Big US Cities.

Run from channel/:  python3 videos/v02_down_payment/build.py [thumb|video|all]
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(CH, "lib"))
sys.path.insert(0, HERE)
from engine import Scene, render, still, write_srt, chapters, txt, box, source, badge, C, money, ease  # noqa
from words import dollars, words  # noqa
import model as M  # noqa

OUT = os.path.join(CH, "out", "v02_down_payment")
os.makedirs(OUT, exist_ok=True)

YEAR = 2024
DF = M.load(YEAR, 2000)
DF["rank"] = np.arange(1, len(DF) + 1)          # 1 = fastest
N = len(DF)
MAXY = DF.years.max()
MED_NOW = DF.years.median()
THEN = DF.dropna(subset=["years_then"]).copy()
MED_THEN = THEN.years_then.median()
THEN["change"] = THEN.years - THEN.years_then
BIGGEST = THEN.sort_values("change", ascending=False).head(5)

SPOKEN = {"New York (Brooklyn)": "Brooklyn, New York", "Washington DC": "Washington, D.C.",
          "St. Louis": "Saint Louis"}


def say(city):
    return SPOKEN.get(city, city)


def yw(x):
    """4.36 -> 'four point four years'"""
    x = round(x, 1)
    return f"{words(int(x))} point {words(int(round(x * 10)) % 10)} years"


def row(city):
    return DF[DF.city == city].iloc[0]


FACTS = dict(year=YEAR, median_now=MED_NOW, median_then=MED_THEN,
             fastest=DF.head(5)[["city", "years"]].values.tolist(),
             slowest=DF.tail(5)[["city", "years"]].values.tolist(),
             biggest_change=BIGGEST[["city", "years_then", "years"]].values.tolist())
json.dump(FACTS, open(os.path.join(OUT, "facts.json"), "w"), indent=2, default=float)

SRC = (f"Home values: Zillow Home Value Index (typical home, {YEAR} avg, county) · Income: Census SAIPE median "
       f"household income {YEAR} via FRED · core county of each metro")
METHOD = "Years = 20% of typical home value ÷ (15% of median household income). No raises, no interest, no price growth."


def header(fig, s):
    txt(fig, 0.04, 0.93, s.upper(), size=22, color=C["muted"], ha="left")


def col(y):
    return C["green"] if y < 5 else (C["amber"] if y < 8 else C["red"])


def prog(c, frac=0.92):
    return min(1.0, c.beat_t / max(0.1, c.beat_d * frac))


# ---------------- scenes ----------------
def d_hook(fig, c):
    d, b = row("Detroit"), row("New York (Brooklyn)")
    a0 = c.bp if c.beat == 0 else 1
    txt(fig, 0.27, 0.72, "DETROIT", size=40, color=C["muted"], alpha=a0)
    txt(fig, 0.27, 0.55, f"{d.years:.1f} yrs", size=120, color=C["green"], alpha=a0)
    if c.beat >= 1:
        a1 = c.bp if c.beat == 1 else 1
        txt(fig, 0.73, 0.72, "BROOKLYN", size=40, color=C["muted"], alpha=a1)
        txt(fig, 0.73, 0.55, f"{b.years:.1f} yrs", size=120, color=C["red"], alpha=a1)
    if c.beat >= 2:
        txt(fig, 0.5, 0.3, "to save a 20% down payment on a typical home", size=36, weight="medium", alpha=c.bp)
        txt(fig, 0.5, 0.2, f"{N} big US cities, ranked", size=44, color=C["amber"], alpha=c.bp)


def d_method(fig, c):
    header(fig, "How I ranked them")
    lines = [("Typical home value", "Zillow Home Value Index"), ("Median household income", "U.S. Census Bureau"),
             ("Save 15% of income a year", "toward a 20% down payment")]
    for i, (k, v) in enumerate(lines[: (2 if c.beat == 0 else 3)]):
        y = 0.74 - i * 0.14
        a = 1 if (c.beat == 1 and i < 2) else ease(c.beat_t / 0.5 - (i if c.beat == 0 else 0) * 0.9)
        box(fig, 0.06, y - 0.055, 0.88, 0.11, C["panel"], alpha=a)
        txt(fig, 0.09, y, k, size=36, ha="left", alpha=a)
        txt(fig, 0.91, y, v, size=28, weight="medium", color=C["muted"], ha="right", alpha=a)
    if c.beat == 1:
        txt(fig, 0.5, 0.25, "years  =  (20% × home value)  ÷  (15% × income)", size=40, color=C["amber"], alpha=c.bp)
    source(fig, SRC)


def page_draw(lo, hi, full=False):
    """Ranks hi..lo (slowest of the page first), bars appear in sync with the list beat."""
    sub = DF[(DF["rank"] >= lo) & (DF["rank"] <= hi)].sort_values("rank", ascending=False)

    def d(fig, c):
        header(fig, f"#{hi} to #{lo}" if lo > 1 else "The top 10: fastest cities")
        txt(fig, 0.96, 0.93, "YEARS TO SAVE 20% DOWN", size=18, color=C["muted"], ha="right")
        shown = len(sub) if full else (0 if c.beat == 0 else min(len(sub), int(prog(c) * len(sub)) + 1))
        for i, (_, r) in enumerate(sub.iterrows()):
            y = 0.83 - i * 0.073
            if i >= shown:
                continue
            a = 1.0
            txt(fig, 0.04, y, f"#{int(r['rank'])}", size=26, color=C["muted"], ha="left", alpha=a)
            txt(fig, 0.1, y, f"{r.city}", size=27, ha="left", alpha=a)
            txt(fig, 0.1, y - 0.027, f"{r.county}, {r.state}", size=14, weight="normal", color=C["muted"], ha="left")
            w = 0.33 * r.years / MAXY
            box(fig, 0.36, y - 0.022, w, 0.044, col(r.years), r=0.006)
            txt(fig, 0.37 + w, y, f"{r.years:.1f}", size=26, ha="left")
            txt(fig, 0.96, y, f"{money(r.value)} home · {money(r.income)} income", size=16, weight="medium",
                color=C["muted"], ha="right")
        if c.beat == 0 and not full:
            txt(fig, 0.5, 0.5, f"#{hi} – #{lo}" if lo > 1 else "TOP 10", size=110, color=C["amber"], alpha=c.bp)
        source(fig, SRC)
    return d, sub


def page_beats(sub, intro):
    items = []
    for _, r in sub.iterrows():
        items.append(f"Number {words(int(r['rank']))}, {say(r.city)}. {yw(r.years)}.")
    return [intro, " ".join(items)]


def d_surprise(fig, c):
    header(fig, "Cheap isn't the same as affordable")
    pairs = [("New Orleans", "Houston"), ("Richmond", "Atlanta")]
    a_, b_ = pairs[min(c.beat, 1)]
    for j, name in enumerate((a_, b_)):
        r = row(name)
        x = 0.06 + j * 0.47
        a = c.bp
        box(fig, x, 0.2, 0.41, 0.6, C["panel"], alpha=a)
        txt(fig, x + 0.205, 0.72, name.upper(), size=36, alpha=a)
        txt(fig, x + 0.205, 0.6, f"Home {money(r.value)}", size=30, weight="medium", alpha=a)
        txt(fig, x + 0.205, 0.51, f"Income {money(r.income)}", size=30, weight="medium", alpha=a)
        txt(fig, x + 0.205, 0.34, f"{r.years:.1f} years", size=64, color=col(r.years), alpha=a)
    source(fig, SRC)


def d_then(fig, c):
    header(fig, f"2000 vs {YEAR}: years to save a down payment")
    t = THEN.sort_values("years")
    ax = fig.add_axes([0.06, 0.12, 0.9, 0.7])
    x = np.arange(len(t))
    p = prog(c) if c.beat == 0 else 1
    ax.scatter(x, t.years_then, color=C["blue"], s=70, label="2000", zorder=3)
    grow = t.years_then + (t.years - t.years_then) * p
    ax.vlines(x, t.years_then, grow, color=C["muted"], lw=2, alpha=0.6)
    ax.scatter(x, grow, color=C["red"], s=70, label=str(YEAR), zorder=3)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(t)} cities, fastest to slowest today", fontsize=18)
    if p >= 1:
        for name in list(BIGGEST.city[:3]) + ["Detroit", "New York (Brooklyn)"]:
            i = list(t.city).index(name)
            ax.annotate(name.replace("New York (Brooklyn)", "Brooklyn"), (x[i], t.years.iloc[i]), xytext=(0, 14),
                        textcoords="offset points", ha="center", color=C["text"], fontsize=16, fontweight="bold")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", color=C["grid"]); ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=16)
    ax.set_ylim(0, MAXY * 1.15)
    ax.set_ylabel("Years", fontsize=18)
    ax.legend(loc="upper left", frameon=False, fontsize=22, labelcolor=C["text"])
    if c.beat >= 1:
        txt(fig, 0.5, 0.86, f"Median city: {MED_THEN:.1f} years in 2000  →  {MED_NOW:.1f} years in {YEAR}", size=32,
            color=C["amber"], alpha=c.bp if c.beat == 1 else 1)
    source(fig, "Zillow ZHVI and Census SAIPE, 2000 and " + str(YEAR) + " (cities with 2000 data)")


def d_levers(fig, c):
    header(fig, "What changes the answer")
    med = MED_NOW
    rows = [("Save 15%, put 20% down", med), ("Save 15%, put 10% down", med / 2),
            ("Save 25%, put 20% down", med * 15 / 25), ("Save 25%, put 10% down", med * 15 / 25 / 2)]
    for i, (k, v) in enumerate(rows[: c.beat + 2]):
        y = 0.72 - i * 0.14
        a = c.bp if i == c.beat + 1 else 1
        txt(fig, 0.06, y, k, size=34, weight="medium", ha="left", alpha=a)
        w = 0.4 * v / med
        box(fig, 0.48, y - 0.04, w, 0.08, col(v), alpha=a)
        txt(fig, 0.49 + w, y, f"{v:.1f} yrs", size=32, ha="left", alpha=a)
    txt(fig, 0.06, 0.86, "For the median city in this ranking", size=24, weight="medium", color=C["muted"], ha="left")
    if c.beat >= 1:
        badge(fig, 0.06, 0.12, " UNDER 20% DOWN USUALLY MEANS PAYING PMI ", size=15)


def d_caveats(fig, c):
    header(fig, "What this doesn't capture")
    items = ["Prices keep rising while you save", "Savings can earn interest or returns",
             "County medians hide cheaper (and pricier) neighborhoods", "Down-payment assistance programs exist"]
    for i, s in enumerate(items):
        a = ease(c.beat_t / 0.4 - i * 1.2)
        txt(fig, 0.08, 0.72 - i * 0.13, "•  " + s, size=36, weight="medium", ha="left", alpha=a)


def d_cta(fig, c):
    if c.beat == 0:
        txt(fig, 0.5, 0.62, "Is your city on the list?", size=76, alpha=c.bp)
        txt(fig, 0.5, 0.47, "Not here? Comment it and I'll run the numbers", size=38, weight="medium",
            color=C["muted"], alpha=c.bp)
    else:
        txt(fig, 0.5, 0.64, "WATCH NEXT", size=30, color=C["muted"])
        txt(fig, 0.5, 0.53, "The real cost of a $400,000 house", size=60, color=C["teal"], alpha=c.bp)
        txt(fig, 0.5, 0.1, "Educational only. Not financial advice. Data & method in the description.",
            size=20, weight="normal", color=C["muted"])


slow5 = DF.tail(5).iloc[::-1]
S = [
    Scene(chapter="Intro", draw=d_hook, beats=[
        f"In Detroit, a typical household could save a twenty percent down payment on a typical home in about "
        f"{yw(row('Detroit').years)}.",
        f"In Brooklyn, it would take {yw(row('New York (Brooklyn)').years)}.",
        f"I ranked {words(N)} of America's biggest cities by how long it takes to save for a house. Your city is "
        "probably on this list, and the chapters are named after the cities, so you can jump straight to it.",
    ]),
    Scene(chapter="How I ranked them", draw=d_method, beats=[
        f"Here's the method. For each city, I took the typical home value from Zillow, and the median household "
        f"income from the Census Bureau, both for twenty twenty-four, in the main county of each metro area.",
        "Then I asked one question. If a household saves fifteen percent of its income every year, how many years "
        "until it has twenty percent of the home's value?",
    ]),
]
PAGES = [(41, 50, "Let's start at the bottom. These are the ten slowest cities on the list."),
         (31, 40, "Numbers forty to thirty-one."),
         (21, 30, "Numbers thirty to twenty-one. We're getting close to the middle."),
         (11, 20, "Numbers twenty to eleven."),
         (1, 10, "And now, the ten fastest cities to save a down payment.")]
for lo, hi, intro in PAGES:
    d, sub = page_draw(lo, hi)
    names = ", ".join(s.replace("New York (Brooklyn)", "Brooklyn") for s in sub.city.head(3))
    chap = f"#{hi}–{lo}: {names}…" if lo > 1 else f"Top 10: {', '.join(sub.city.tail(3)[::-1])}…"
    S.append(Scene(chapter=chap, draw=d, live=True, beats=page_beats(sub, intro)))
    if lo == 41:
        S.append(Scene(draw=page_draw(lo, hi, full=True)[0], beats=[
            "Notice what the bottom of the list has in common. Most are coastal cities, where incomes are high, "
            "but home prices are even higher. San Jose has the highest median income on this entire list, and it "
            "still takes more than twelve years."]))

nola, hou, ric, atl = row("New Orleans"), row("Houston"), row("Richmond"), row("Atlanta")
S += [
    Scene(chapter="Cheap isn't affordable", draw=d_surprise, beats=[
        f"Here's what surprised me. A cheap house doesn't mean an affordable one. Homes in New Orleans are cheaper "
        f"than in Houston, about {dollars(nola.value)} against {dollars(hou.value)}. But incomes in New Orleans are "
        f"much lower, so it actually takes longer to save there: {yw(nola.years)}, against {yw(hou.years)}.",
        f"Same story with Richmond and Atlanta. Richmond's homes cost less, but it takes {yw(ric.years)} to save, "
        f"compared to {yw(atl.years)} in Atlanta. What matters is price compared to income.",
    ]),
    Scene(chapter="2000 vs today", draw=d_then, beats=[
        f"Now let's go back to the year two thousand. Blue is how long it took then. Red is twenty twenty-four.",
        f"In the median city, saving a down payment went from {yw(MED_THEN)} to {yw(MED_NOW)}. Some of the "
        f"biggest jumps were in {say(BIGGEST.iloc[0].city)}, {say(BIGGEST.iloc[1].city)}, and "
        f"{say(BIGGEST.iloc[2].city)}. If buying a home feels harder than it did for your parents, the data "
        "says you're not imagining it.",
    ]),
    Scene(chapter="What changes the answer", draw=d_levers, anim=1.0, beats=[
        f"So what can you actually change? For the median city here, saving fifteen percent for a twenty percent "
        f"down payment takes about {yw(MED_NOW)}. Put ten percent down instead, and that's cut in half.",
        "Save twenty-five percent of your income, and it drops further.",
        "Do both, and you're looking at under two years in the median city. Just remember, putting down less than "
        "twenty percent usually means paying private mortgage insurance.",
    ]),
    Scene(chapter="What this misses", draw=d_caveats, live=True, beats=[
        "A few honest caveats. Home prices keep rising while you save, which makes this harder. Savings can earn "
        "interest, which makes it easier. County medians hide neighborhoods that are much cheaper, or much more "
        "expensive. And many cities and states have down payment assistance programs worth checking.",
    ]),
    Scene(chapter="Your city", draw=d_cta, beats=[
        "Is your city on the list? Tell me where you live and how many years it would take you. And if your city "
        "isn't here, comment it, and I'll run the numbers.",
        "And if you want to see what that house really costs once you've bought it, watch this one next. It's "
        "not what you think. This video is for education, not financial advice. See you in the next one.",
    ]),
]


def thumbnail(fig):
    from matplotlib.patches import Rectangle
    txt(fig, 0.05, 0.84, "YEARS TO SAVE A DOWN PAYMENT", size=40, ha="left", color=C["muted"])
    top = [(row("Detroit"), C["green"]), (row("New York (Brooklyn)"), C["red"])]
    for i, (r, cc) in enumerate(top):
        y = 0.6 - i * 0.3
        nm = "BROOKLYN" if "Brooklyn" in r.city else r.city.upper()
        txt(fig, 0.05, y, nm, size=64, ha="left")
        txt(fig, 0.95, y, f"{r.years:.0f} YRS" if r.years > 10 else f"{r.years:.1f} YRS", size=110, ha="right", color=cc)
    txt(fig, 0.05, 0.08, " WHERE DOES YOUR CITY RANK? ", size=40, ha="left", color=C["bg"],
        bbox=dict(boxstyle="round,pad=0.3", facecolor=C["amber"], edgecolor="none"))


def description(chaps):
    table = "\n".join(f"{int(r['rank'])}. {r.city}: {r.years:.1f} yrs (home {money(r.value)}, income {money(r.income)})"
                      for _, r in DF.iterrows())
    return f"""How long does it take to save a 20% down payment in your city? I ranked {N} big US cities using Zillow home values and Census income data.

Find your city in the chapters. Not on the list? Comment it and I'll run the numbers.

CHAPTERS
{chr(10).join(chaps)}

FULL RANKING ({YEAR}, fastest first)
{table}

Median city: {MED_THEN:.1f} years in 2000 → {MED_NOW:.1f} years in {YEAR}.

METHOD
Years = 20% of the typical home value ÷ 15% of median household income. Typical home value is the {YEAR} average of the Zillow Home Value Index (all homes, mid-tier, smoothed, seasonally adjusted) for the core county of each metro area. Income is the Census SAIPE {YEAR} median household income for the same county. No raises, no interest on savings, no home-price growth while saving.

SOURCES
• Zillow Home Value Index (ZHVI), county level: https://www.zillow.com/research/data/
• Census SAIPE median household income by county, via FRED (series MHI…A052NCEN): https://fred.stlouisfed.org/
This video is for educational purposes only and is not financial advice.
"""


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(json.dumps(FACTS, indent=1, default=float))
    if only in ("all", "thumb"):
        still(thumbnail, os.path.join(OUT, "thumbnail.png"))
    if only in ("all", "video"):
        total, work = render(S, os.path.join(OUT, "v02_down_payment.mp4"))
        write_srt(S, os.path.join(OUT, "captions.srt"))
        open(os.path.join(OUT, "description.txt"), "w").write(description(chapters(S)))
        print(f"rendered {total:.1f}s")
