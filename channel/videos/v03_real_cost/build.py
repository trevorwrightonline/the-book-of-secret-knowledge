"""Video 3: The Real Cost of a $400,000 House (It's Not $400,000).

Run:  python3 videos/v03_real_cost/build.py            (from channel/)
Outputs land in channel/out/v03_real_cost/.
"""
import os, sys, json
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon, Rectangle, Wedge

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(CH, "lib"))
from engine import Scene, render, still, write_srt, chapters, txt, box, source, badge, C, money, ease  # noqa
from words import dollars, pct, words  # noqa

OUT = os.path.join(CH, "out", "v03_real_cost")
os.makedirs(OUT, exist_ok=True)

# ---------------- data ----------------
rates = pd.read_csv(os.path.join(CH, "data", "MORTGAGE30US.csv"), parse_dates=["observation_date"])
rates = rates.dropna()
latest = rates.iloc[-1]
RATE = float(latest["MORTGAGE30US"])
RATE_DATE = latest["observation_date"]

PRICE = 400_000
DOWN = 0.20 * PRICE
LOAN = PRICE - DOWN
CLOSING = 0.03 * PRICE
YEARS = 30
N = YEARS * 12
# NAHB analysis of 2024 ACS: aggregate RE taxes / aggregate owner-occupied value
TAX_US, TAX_IL, TAX_HI = 8.88 / 1000, 17.93 / 1000, 3.08 / 1000
INSURANCE = 2_400          # assumption, per year
MAINT = 0.01 * PRICE       # 1% rule, per year
OPP_RETURN = 0.07          # assumption


def amortize(rate_pct, loan=LOAN, n=N):
    r = rate_pct / 100 / 12
    pmt = loan * r / (1 - (1 + r) ** -n)
    bal, ints, prins = loan, [], []
    for _ in range(n):
        i = bal * r
        p = pmt - i
        bal -= p
        ints.append(i)
        prins.append(p)
    return pmt, np.array(ints), np.array(prins)


PMT, INTS, PRINS = amortize(RATE)
TOTAL_PAID = PMT * N
INTEREST = INTS.sum()
Y_INT = INTS.reshape(YEARS, 12).sum(1)
Y_PRIN = PRINS.reshape(YEARS, 12).sum(1)
CROSS_M = int(np.argmax(PRINS > INTS)) + 1
CROSS_Y = (CROSS_M - 1) // 12 + 1
TAX_Y = TAX_US * PRICE
TAX_30 = TAX_Y * YEARS
INS_30 = INSURANCE * YEARS
MAINT_30 = MAINT * YEARS
UPFRONT = DOWN + CLOSING
OPP_VALUE = UPFRONT * (1 + OPP_RETURN) ** YEARS
TOTAL = DOWN + LOAN + INTEREST + CLOSING + TAX_30 + INS_30 + MAINT_30
RATE_TABLE = [(r, amortize(r)[1].sum()) for r in (5.0, 6.0, round(RATE - 1, 2), RATE, 8.0)]
SAVE_1PT = INTEREST - amortize(RATE - 1)[1].sum()

FACTS = dict(rate=RATE, rate_date=str(RATE_DATE.date()), pmt=PMT, total_paid=TOTAL_PAID,
             interest=INTEREST, y1_int=Y_INT[0], y1_prin=Y_PRIN[0], cross_year=CROSS_Y,
             tax_year=TAX_Y, tax_30=TAX_30, ins_30=INS_30, maint_30=MAINT_30,
             opp_value=OPP_VALUE, total=TOTAL, multiple=TOTAL / PRICE,
             rate_table=RATE_TABLE, save_1pt=SAVE_1PT)
json.dump(FACTS, open(os.path.join(OUT, "facts.json"), "w"), indent=2, default=float)

SRC_RATE = f"Source: Freddie Mac Primary Mortgage Market Survey via FRED (MORTGAGE30US), week of {RATE_DATE:%b %-d, %Y}"
SRC_TAX = "Source: NAHB analysis of 2024 American Community Survey (effective rate = aggregate taxes / aggregate home value)"
date_words = f"{RATE_DATE:%B} {words(RATE_DATE.day)}, twenty twenty-{words(RATE_DATE.year - 2020)}"
rate_words = pct(RATE)

def times_phrase(m):
    whole, frac = int(m), m % 1
    if frac >= 0.85:
        return f"almost {words(whole + 1)} times"
    if frac <= 0.15:
        return f"about {words(round(m))} times"
    if 0.4 <= frac <= 0.6:
        return f"about {words(whole)} and a half times"
    return f"more than {words(whole)} times"


# ---------------- visuals ----------------
def header(fig, s):
    txt(fig, 0.04, 0.93, s.upper(), size=22, color=C["muted"], ha="left")


def house(fig, cx, cy, s, color, alpha=1.0):
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ar = fig.get_figwidth() / fig.get_figheight()
    w, h = s / ar, s
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h * 0.6, fill=False, lw=6, ec=color, alpha=alpha))
    ax.add_patch(Polygon([(cx - w * 0.62, cy + h * 0.1), (cx, cy + h * 0.55), (cx + w * 0.62, cy + h * 0.1)],
                         closed=True, fill=False, lw=6, ec=color, alpha=alpha, joinstyle="round"))
    ax.add_patch(Rectangle((cx - w * 0.1, cy - h / 2), w * 0.2, h * 0.32, fill=True, fc=color, alpha=alpha))


def big_number(fig, y, value, size=120, color=None, prefix="", suffix="", p=1.0, start=0):
    v = start + (value - start) * p
    txt(fig, 0.5, y, f"{prefix}{money(v)}{suffix}", size=size, color=color or C["text"])


def d_hook(fig, c):
    house(fig, 0.5, 0.74, 0.16, C["teal"], alpha=min(1, c.bp * 1.5) if c.beat == 0 else 1)
    a = c.bp if c.beat == 0 else 1
    txt(fig, 0.5, 0.48, "$400,000", size=130, alpha=a)
    txt(fig, 0.5, 0.36, "LISTED PRICE", size=24, color=C["muted"], alpha=a)
    if c.beat >= 1:
        p = c.bp if c.beat == 1 else 1
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.plot([0.27, 0.27 + 0.46 * p], [0.48, 0.48], color=C["red"], lw=10, solid_capstyle="round")
        txt(fig, 0.5, 0.21, money(TOTAL * p), size=96, color=C["red"])
        txt(fig, 0.5, 0.12, "WHAT YOU REALLY PAY OVER 30 YEARS", size=22, color=C["red"], alpha=p)
    if c.beat >= 2:
        badge(fig, 0.04, 0.93, " BUILT LINE BY LINE FROM REAL DATA ", color=C["teal"], size=18)


def d_setup(fig, c):
    header(fig, "The example")
    rows = [("Home price", money(PRICE)), ("Down payment (20%)", money(DOWN)), ("Loan amount", money(LOAN)),
            ("Rate (30-yr fixed)", f"{RATE:.2f}%"), ("Term", "30 years")]
    show = 3 if c.beat == 0 else 5
    for i, (k, v) in enumerate(rows[:show]):
        y = 0.76 - i * 0.12
        a = 1.0 if (c.beat == 1 and i < 3) else ease(c.beat_t / 0.5 - i * 0.6 if c.beat == 0 else c.beat_t / 0.5 - (i - 3) * 0.6)
        box(fig, 0.05, y - 0.045, 0.42, 0.09, C["panel"], alpha=a)
        txt(fig, 0.07, y, k, size=30, weight="medium", color=C["muted"], ha="left", alpha=a)
        txt(fig, 0.45, y, v, size=34, ha="right", alpha=a,
            color=C["amber"] if k.startswith("Rate") else C["text"])
    if c.beat == 1:
        ax = fig.add_axes([0.55, 0.18, 0.41, 0.6])
        d = rates[rates.observation_date >= "2000-01-01"]
        k = max(2, int(len(d) * c.bp))
        ax.plot(d.observation_date.iloc[:k], d.MORTGAGE30US.iloc[:k], color=C["amber"], lw=3)
        ax.set_xlim(d.observation_date.iloc[0], d.observation_date.iloc[-1])
        ax.set_ylim(0, d.MORTGAGE30US.max() * 1.15)
        ax.grid(color=C["grid"], lw=1); ax.set_axisbelow(True)
        for s in ax.spines.values(): s.set_visible(False)
        ax.tick_params(labelsize=16)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
        ax.set_title("30-year fixed mortgage rate, 2000 to today", color=C["text"], fontsize=20, loc="left", pad=14)
        if c.bp >= 1:
            ax.scatter([d.observation_date.iloc[-1]], [RATE], s=140, color=C["amber"], zorder=5)
            ax.annotate(f"{RATE:.2f}%", (d.observation_date.iloc[-1], RATE), xytext=(-90, 25),
                        textcoords="offset points", color=C["amber"], fontsize=24, fontweight="bold")
        source(fig, SRC_RATE + "   ·   Educational example, not financial advice")


def d_closing(fig, c):
    header(fig, "Cost 1 · Closing costs")
    fees = ["Lender & origination fees", "Title insurance", "Appraisal & inspection", "Prepaid taxes & insurance"]
    for i, f in enumerate(fees):
        a = 1 if c.beat == 1 else ease(c.beat_t / 0.4 - i * 0.9)
        txt(fig, 0.08, 0.72 - i * 0.1, "•  " + f, size=34, weight="medium", ha="left", alpha=a)
    if c.beat == 1:
        txt(fig, 0.72, 0.56, money(CLOSING * c.bp), size=110, color=C["gray"])
        txt(fig, 0.72, 0.43, "typically a few % of the price", size=24, weight="medium", color=C["muted"])
        badge(fig, 0.63, 0.31, " ASSUMPTION: 3% OF PRICE ")


def d_payment(fig, c):
    header(fig, "Cost 2 · The mortgage")
    txt(fig, 0.5, 0.66, money(PMT * (c.bp if c.beat == 0 else 1)), size=130)
    txt(fig, 0.5, 0.53, "PER MONTH  ·  PRINCIPAL + INTEREST ONLY", size=24, color=C["muted"])
    if c.beat == 1:
        txt(fig, 0.5, 0.40, "× 360 months =", size=36, weight="medium", color=C["muted"], alpha=c.bp)
        txt(fig, 0.5, 0.26, money(TOTAL_PAID * c.bp), size=100, color=C["red"])
    source(fig, f"Loan {money(LOAN)} at {RATE:.2f}%, 30-year fixed. Standard amortization formula.")


def d_year1(fig, c):
    header(fig, "Where year 1 of payments goes")
    y1 = Y_INT[0] + Y_PRIN[0]
    txt(fig, 0.5, 0.75, f"Year 1 payments: {money(y1)}", size=48)
    x0, w = 0.1, 0.8
    if c.beat == 0:
        box(fig, x0, 0.45, w * c.bp, 0.14, C["gray"])
    else:
        fp = Y_PRIN[0] / y1
        box(fig, x0, 0.45, w * fp, 0.14, C["green"])
        box(fig, x0 + w * fp, 0.45, w * (1 - fp) * c.bp, 0.14, C["red"])
        txt(fig, x0, 0.36, f"Principal {money(Y_PRIN[0])}", size=34, color=C["green"], ha="left")
        txt(fig, x0 + w, 0.36, f"Interest {money(Y_INT[0])}", size=34, color=C["red"], ha="right", alpha=c.bp)
        txt(fig, 0.5, 0.2, f"{Y_INT[0] / y1:.0%} of your year-1 payments go to interest", size=36,
            weight="medium", alpha=c.bp)


def d_amort(fig, c):
    header(fig, "30 years of payments, year by year")
    ax = fig.add_axes([0.07, 0.16, 0.86, 0.62])
    k = YEARS if c.beat > 0 else max(1, int(YEARS * c.bp))
    yrs = np.arange(1, YEARS + 1)
    ax.bar(yrs[:k], Y_PRIN[:k], color=C["green"], width=0.75, label="Principal")
    ax.bar(yrs[:k], Y_INT[:k], bottom=Y_PRIN[:k], color=C["red"], width=0.75, label="Interest")
    ax.set_xlim(0.3, YEARS + 0.7); ax.set_ylim(0, (Y_INT[0] + Y_PRIN[0]) * 1.2)
    for s in ax.spines.values(): s.set_visible(False)
    ax.grid(axis="y", color=C["grid"]); ax.set_axisbelow(True)
    ax.tick_params(labelsize=16)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:.0f}k")
    ax.set_xlabel("Year of loan", fontsize=18)
    ax.legend(loc="upper left", frameon=False, fontsize=20, labelcolor=C["text"], ncol=2)
    if c.beat >= 1:
        a = c.bp if c.beat == 1 else 1
        ax.axvline(CROSS_Y, color=C["amber"], lw=3, ls="--", alpha=a)
        ax.text(CROSS_Y - 0.4, (Y_INT[0] + Y_PRIN[0]) * 1.08, f"Year {CROSS_Y}: principal finally beats interest",
                color=C["amber"], fontsize=22, fontweight="bold", alpha=a, ha="right")
    if c.beat == 2:
        txt(fig, 0.5, 0.86, f"Total interest: {money(INTEREST * c.bp)}", size=44, color=C["red"])
    source(fig, f"{money(LOAN)} loan at {RATE:.2f}%, 30-year fixed")


def d_tax(fig, c):
    header(fig, "Cost 3 · Property tax")
    txt(fig, 0.5, 0.7, "0.89% of home value, every year", size=50, alpha=c.bp if c.beat == 0 else 1)
    if c.beat == 1:
        txt(fig, 0.3, 0.45, money(TAX_Y * c.bp), size=90, color=C["amber"])
        txt(fig, 0.3, 0.34, "PER YEAR", size=22, color=C["muted"])
        txt(fig, 0.7, 0.45, money(TAX_30 * c.bp), size=90, color=C["amber"])
        txt(fig, 0.7, 0.34, "OVER 30 YEARS (FLAT VALUE: A LOW ESTIMATE)", size=22, color=C["muted"])
        source(fig, SRC_TAX)


def d_states(fig, c):
    header(fig, "Same house, different state")
    data = [("Hawaii (lowest)", TAX_HI, C["green"]), ("US average", TAX_US, C["amber"]), ("Illinois (highest)", TAX_IL, C["red"])]
    show = 2 if c.beat == 0 else 3
    mx = TAX_IL * PRICE * YEARS
    for i, (name, r, col) in enumerate(data[:show]):
        y = 0.66 - i * 0.16
        p = 1 if (c.beat == 1 and i < 2) else c.bp
        v = r * PRICE * YEARS
        txt(fig, 0.06, y, name, size=30, weight="medium", ha="left")
        box(fig, 0.3, y - 0.045, 0.5 * v / mx * p, 0.09, col)
        txt(fig, 0.31 + 0.5 * v / mx * p, y, f"{money(v * p)}  ({money(r * PRICE)}/yr)", size=26, ha="left")
    txt(fig, 0.5, 0.82, "Property tax on a $400,000 home over 30 years", size=34)
    if c.beat == 1 and c.bp >= 1:
        txt(fig, 0.5, 0.17, f"Difference: {money((TAX_IL - TAX_HI) * PRICE * YEARS)}", size=44, color=C["red"])
    source(fig, SRC_TAX)


def d_insurance(fig, c):
    header(fig, "Cost 4 · Homeowners insurance")
    txt(fig, 0.5, 0.72, "Required by your lender  ·  varies hugely by state", size=36, weight="medium",
        color=C["muted"], alpha=c.bp if c.beat == 0 else 1)
    if c.beat == 1:
        txt(fig, 0.3, 0.47, money(INSURANCE * c.bp), size=90, color=C["blue"])
        txt(fig, 0.3, 0.36, "PER YEAR", size=22, color=C["muted"])
        txt(fig, 0.7, 0.47, money(INS_30 * c.bp), size=90, color=C["blue"])
        txt(fig, 0.7, 0.36, "OVER 30 YEARS", size=22, color=C["muted"])
        badge(fig, 0.36, 0.2, " ASSUMPTION: GET A REAL QUOTE BEFORE YOU OFFER ")


def d_maint(fig, c):
    header(fig, "Cost 5 · The one first-time buyers forget")
    if c.beat == 0:
        txt(fig, 0.5, 0.5, "MAINTENANCE", size=140, color=C["purple"], alpha=c.bp)
        return
    items = ["Roof", "Water heater", "HVAC", "Appliances", "Plumbing", "Paint & flooring"]
    for i, it in enumerate(items):
        col, row = i % 3, i // 3
        a = 1 if c.beat == 2 else ease(c.beat_t / 0.35 - i * 0.6)
        x, y = 0.08 + col * 0.29, 0.62 - row * 0.17
        box(fig, x, y, 0.26, 0.12, C["panel"], alpha=a)
        txt(fig, x + 0.13, y + 0.06, it, size=32, alpha=a)
    if c.beat == 2:
        txt(fig, 0.5, 0.27, f"1% rule  →  {money(MAINT)}/yr  →  {money(MAINT_30 * c.bp)} over 30 years",
            size=40, color=C["purple"])
        badge(fig, 0.04, 0.12, " RULE OF THUMB · OLDER HOMES OFTEN NEED MORE ")


PARTS = [("Down payment", DOWN, C["teal"]), ("Loan principal", LOAN, C["green"]),
         ("Interest", INTEREST, C["red"]), ("Closing costs", CLOSING, C["gray"]),
         ("Property tax", TAX_30, C["amber"]), ("Insurance", INS_30, C["blue"]),
         ("Maintenance", MAINT_30, C["purple"])]


def d_total(fig, c):
    header(fig, "The real price")
    ax = fig.add_axes([0.05, 0.08, 0.46, 0.82]); ax.set_axis_off(); ax.set_aspect("equal")
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1)
    prog = min(1.0, c.beat_t / (c.beat_d * 0.9)) if c.beat == 0 else 1.0
    shown = PARTS[: max(1, int(np.ceil(prog * len(PARTS))))]
    ang = 90
    for name, v, col in shown:
        span = 360 * v / TOTAL
        ax.add_patch(Wedge((0, 0), 1, ang - span, ang, width=0.32, fc=col, ec=C["bg"], lw=3))
        ang -= span
    for i, (name, v, col) in enumerate(shown):
        y = 0.82 - i * 0.085
        box(fig, 0.56, y - 0.018, 0.022, 0.036, col, r=0.004)
        txt(fig, 0.6, y, name, size=28, weight="medium", ha="left")
        txt(fig, 0.95, y, money(v), size=28, ha="right")
    if c.beat == 1:
        txt(fig, 0.28, 0.52, money(TOTAL * c.bp), size=50, color=C["text"])
        txt(fig, 0.28, 0.44, f"≈ {TOTAL / PRICE:.1f}× the sticker price", size=24, color=C["muted"])
        txt(fig, 0.775, 0.16, f"TOTAL  {money(TOTAL)}", size=36, color=C["red"], alpha=c.bp)


def d_opp(fig, c):
    header(fig, "The cost that never sends a bill")
    txt(fig, 0.5, 0.82, f"{money(UPFRONT)} paid up front (down payment + closing)", size=38)
    if c.beat == 1:
        ax = fig.add_axes([0.1, 0.17, 0.8, 0.52])
        yrs = np.arange(0, YEARS + 1)
        vals = UPFRONT * (1 + OPP_RETURN) ** yrs
        k = max(2, int(len(yrs) * c.bp))
        ax.fill_between(yrs[:k], vals[:k], color=C["teal"], alpha=0.25)
        ax.plot(yrs[:k], vals[:k], color=C["teal"], lw=4)
        ax.set_xlim(0, YEARS); ax.set_ylim(0, vals[-1] * 1.15)
        for s in ax.spines.values(): s.set_visible(False)
        ax.grid(axis="y", color=C["grid"]); ax.tick_params(labelsize=16)
        ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:.0f}k")
        ax.set_xlabel("Years", fontsize=18)
        if c.bp >= 1:
            ax.annotate(money(OPP_VALUE), (YEARS, vals[-1]), xytext=(-260, 0), textcoords="offset points",
                        color=C["teal"], fontsize=34, fontweight="bold")
        badge(fig, 0.04, 0.08, " ASSUMPTION: 7%/YR RETURN · NOT A PROMISE · NOT ADDED TO TOTAL ")


def d_rates(fig, c):
    header(fig, "The biggest lever: your rate")
    txt(fig, 0.5, 0.84, "Total interest on the same $320,000 loan", size=36)
    mx = max(v for _, v in RATE_TABLE)
    p = c.bp if c.beat == 0 else 1
    for i, (r, v) in enumerate(RATE_TABLE):
        y = 0.7 - i * 0.12
        col = C["amber"] if abs(r - RATE) < 1e-9 else (C["green"] if r < RATE else C["red"])
        txt(fig, 0.12, y, f"{r:.2f}%", size=32, ha="right", color=col)
        box(fig, 0.15, y - 0.04, 0.6 * v / mx * p, 0.08, col)
        txt(fig, 0.16 + 0.6 * v / mx * p, y, money(v * p), size=28, ha="left")
    if c.beat == 1:
        txt(fig, 0.5, 0.08, f"1 point lower saves ≈ {money(SAVE_1PT)}", size=40, color=C["green"], alpha=c.bp)


TIPS = ["Get quotes from at least 3 lenders", "Put 20% down to avoid PMI",
        "Check (and appeal) your tax assessment", "Get insurance quotes before you offer",
        "Start a maintenance fund on day one"]


def d_tips(fig, c):
    header(fig, "5 ways to shrink the real price")
    for i, t in enumerate(TIPS[: c.beat + 1]):
        y = 0.76 - i * 0.13
        a = c.bp if i == c.beat else 1
        box(fig, 0.08, y - 0.05, 0.84, 0.1, C["panel"], alpha=a)
        txt(fig, 0.11, y, f"{i + 1}", size=40, color=C["green"], alpha=a)
        txt(fig, 0.15, y, t, size=36, weight="medium", ha="left", alpha=a)


def d_fair(fig, c):
    header(fig, "To be fair")
    txt(fig, 0.5, 0.62, "You own the home at the end.", size=54, alpha=c.bp)
    txt(fig, 0.5, 0.5, "Renters pay for housing too.", size=54, alpha=c.bp)
    txt(fig, 0.5, 0.3, "Sticker price ≠ real price", size=64, color=C["amber"], alpha=ease(c.beat_t / 1.2 - 3))


def d_cta(fig, c):
    if c.beat == 0:
        txt(fig, 0.5, 0.6, "What did YOU think it cost?", size=76, alpha=c.bp)
        txt(fig, 0.5, 0.45, "Comment your guess + your city", size=40, weight="medium", color=C["muted"], alpha=c.bp)
    else:
        txt(fig, 0.5, 0.64, "NEXT", size=30, color=C["muted"])
        txt(fig, 0.5, 0.53, "Rent vs Buy: 30 years of real data", size=64, color=C["teal"], alpha=c.bp)
        txt(fig, 0.5, 0.1, "Educational only. Not financial advice. Sources & method in the description.",
            size=20, weight="normal", color=C["muted"])


# ---------------- script ----------------
S = [
    Scene(chapter="Intro", draw=d_hook, beats=[
        "This house is listed at four hundred thousand dollars.",
        f"But buy it with a normal thirty-year mortgage, and what you'll really pay over thirty years is closer to "
        f"{dollars(TOTAL)}. That's not a typo.",
        "Let's build the real price, one line at a time, using real data. And stay to the end, because one of these "
        "costs is the one first-time buyers almost never budget for.",
    ]),
    Scene(chapter="The example", draw=d_setup, beats=[
        "Here's our example. A four hundred thousand dollar home. You put twenty percent down, that's eighty "
        "thousand dollars, so you borrow three hundred twenty thousand.",
        f"The interest rate is {rate_words}. That's the national average for a thirty-year fixed mortgage, in "
        f"Freddie Mac's weekly survey for {date_words}. Every assumption is on screen, and every source is in the "
        "description.",
    ]),
    Scene(chapter="Closing costs", draw=d_closing, beats=[
        "Before you even get the keys, there are closing costs. Lender fees, title insurance, the appraisal, and "
        "prepaid taxes and insurance.",
        "These usually run a few percent of the price. We'll assume three percent, which is twelve thousand "
        "dollars. Your number will depend on your state and your lender.",
    ]),
    Scene(chapter="The monthly payment", draw=d_payment, beats=[
        f"Now the mortgage itself. At {rate_words}, the monthly payment on a three hundred twenty thousand dollar "
        f"loan is about {dollars(PMT)}. And that's just principal and interest, before taxes and insurance.",
        f"Make that payment three hundred sixty times, and you'll have paid the bank about {dollars(TOTAL_PAID)}.",
    ]),
    Scene(chapter="Where year one goes", draw=d_year1, beats=[
        f"Here's the part that surprises people. In year one, you'll pay about "
        f"{dollars(Y_INT[0] + Y_PRIN[0])} in mortgage payments.",
        f"But only about {dollars(Y_PRIN[0])} of that goes toward actually owning the house. The other "
        f"{dollars(Y_INT[0])}, about {words(round(100 * Y_INT[0] / (Y_INT[0] + Y_PRIN[0])))} percent, is interest.",
    ]),
    Scene(draw=d_amort, anim=2.5, beats=[
        "That balance shifts slowly. Each month, a little more of your payment goes to principal, and a little "
        "less to interest.",
        f"At this rate, the principal part of your payment doesn't overtake the interest part until year "
        f"{words(CROSS_Y)}.",
        f"By the end of thirty years, you'll have paid about {dollars(INTEREST)} in interest alone."
        + (" That's more than the three hundred twenty thousand dollars you borrowed." if INTEREST > LOAN else ""),
    ]),
    Scene(chapter="Property tax", draw=d_tax, beats=[
        "Next: property tax. You pay it every year you own the home, even after the mortgage is paid off.",
        f"Nationally, homeowners pay about zero point eight nine percent of their home's value each year, according "
        f"to the National Association of Home Builders' analysis of twenty twenty-four Census data. On this house, "
        f"that's about {dollars(TAX_Y)} a year, or about {dollars(TAX_30)} over thirty years. And that assumes the "
        "home's value never goes up, so the real number is probably higher.",
    ]),
    Scene(draw=d_states, beats=[
        f"But where you live changes this a lot. Put the same house in Hawaii, the state with the lowest effective "
        f"rate, and you'd pay about {dollars(TAX_HI * PRICE)} a year.",
        f"In Illinois, the highest, it's about {dollars(TAX_IL * PRICE)} a year. Over thirty years, that's a "
        f"difference of about {dollars((TAX_IL - TAX_HI) * PRICE * YEARS)}, for the exact same house.",
    ]),
    Scene(chapter="Insurance", draw=d_insurance, beats=[
        "Then there's homeowners insurance. Your lender will require it, and premiums vary enormously by state, "
        "especially where hurricanes, wildfires, or hail are common.",
        "For this example, we'll assume two thousand four hundred dollars a year. Treat that as a placeholder, and "
        "get a real quote before you make an offer. Over thirty years, that's seventy-two thousand dollars.",
    ]),
    Scene(chapter="The forgotten cost", draw=d_maint, beats=[
        "And here's the cost first-time buyers almost never budget for. Maintenance.",
        "Roofs, water heaters, air conditioning, appliances, plumbing, paint. Nobody sends you a monthly bill for "
        "it, so it's easy to forget, until something breaks.",
        "A common rule of thumb is to set aside one percent of the home's value every year. On this house, that's "
        "four thousand dollars a year, or a hundred twenty thousand dollars over thirty years. Older homes often "
        "need more.",
    ]),
    Scene(chapter="The real total", draw=d_total, live=True, beats=[
        f"So let's add it all up. Down payment, eighty thousand. Loan principal, three hundred twenty thousand. "
        f"Interest, {dollars(INTEREST)}. Closing costs, twelve thousand. Property tax, {dollars(TAX_30)}. "
        "Insurance, seventy-two thousand. And maintenance, a hundred twenty thousand.",
        f"The real cost of this four hundred thousand dollar house, over thirty years, is about {dollars(TOTAL)}. "
        f"That's {times_phrase(TOTAL / PRICE)} the sticker price.",
    ]),
    Scene(chapter="Opportunity cost", draw=d_opp, anim=2.5, beats=[
        f"There's one more cost that never shows up on a bill. The {dollars(UPFRONT)} you paid up front, the down "
        "payment plus closing costs, could have been invested instead.",
        f"If it grew at seven percent a year, which is an assumption, not a promise, it would be worth about "
        f"{dollars(OPP_VALUE)} after thirty years. That's called opportunity cost. I'm not adding it to the total, "
        "because the house builds value too, but it belongs in the decision.",
    ]),
    Scene(chapter="How rates change it", draw=d_rates, anim=1.6, beats=[
        "The biggest lever you control is the interest rate. Here's the total interest on the same loan at "
        "different rates.",
        f"At five percent, you'd pay about {dollars(RATE_TABLE[0][1])}. At six, about {dollars(RATE_TABLE[1][1])}. "
        f"At today's {rate_words}, about {dollars(INTEREST)}. Even one percentage point lower would save you "
        f"roughly {dollars(SAVE_1PT)} over the life of the loan.",
    ]),
    Scene(chapter="5 ways to cut it", draw=d_tips, anim=0.6, beats=[
        "So how do you shrink the real price? One. Get quotes from at least three lenders. Rates and fees vary, "
        "and comparing is free.",
        "Two. Put twenty percent down if you can, so you avoid private mortgage insurance, a cost we didn't even "
        "include here.",
        "Three. Check your property tax assessment, and appeal it if it looks too high.",
        "Four. Get insurance quotes before you make an offer, not after.",
        "And five. Start a maintenance fund on day one, so a broken water heater is an expense, not an emergency.",
    ]),
    Scene(draw=d_fair, live=True, beats=[
        "Now, to be fair, none of this makes buying a bad deal. After thirty years, you own the home, and it's "
        "likely worth a lot more than you paid. And renters pay for housing too. The point today is simple. The "
        "sticker price is not the price.",
    ]),
    Scene(chapter="Your turn", draw=d_cta, beats=[
        "Before you watched this, what did you think a four hundred thousand dollar house really cost? Tell me in "
        "the comments, along with your city.",
        "Next, I'm running thirty years of real numbers on renting versus buying. Subscribe so you don't miss it. "
        "This video is for education, not financial advice. The full method and every source are in the "
        "description. See you in the next one.",
    ]),
]

# running "real cost so far" counter, top-right: (scene index, beat) -> value added
HUD_ADD = {2: (1, CLOSING), 5: (2, INTEREST), 6: (1, TAX_30), 8: (1, INS_30), 9: (2, MAINT_30)}
HUD_SCENES = range(1, 10)


def hud(fig, c, si):
    if si not in HUD_SCENES:
        return
    base = PRICE + sum(v for s, (_, v) in HUD_ADD.items() if s < si)
    if si in HUD_ADD:
        b, v = HUD_ADD[si]
        if c.beat > b:
            base += v
        elif c.beat == b:
            base += v * c.bp
    box(fig, 0.73, 0.875, 0.245, 0.1, C["panel"])
    txt(fig, 0.745, 0.95, "REAL COST SO FAR", size=15, color=C["muted"], ha="left")
    txt(fig, 0.745, 0.905, money(base), size=34, color=C["red"], ha="left")


def thumbnail(fig):
    txt(fig, 0.06, 0.78, "$400,000", size=120, ha="left", color=C["text"])
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.plot([0.05, 0.69], [0.79, 0.77], color=C["red"], lw=16, solid_capstyle="round")
    txt(fig, 0.06, 0.44, f"${TOTAL / 1e6:.2f}M", size=190, ha="left", color=C["red"])
    txt(fig, 0.065, 0.14, "THE REAL PRICE", size=60, ha="left", color=C["amber"])
    house(fig, 0.87, 0.42, 0.26, C["teal"])


def description(chaps):
    return f"""A $400,000 house doesn't cost $400,000. Here's the real 30-year price, built line by line from public data: closing costs, mortgage interest, property tax, insurance and maintenance.

What did you think it cost? Comment your guess and your city.

CHAPTERS
{chr(10).join(chaps)}

THE NUMBERS
• Price {money(PRICE)}, 20% down ({money(DOWN)}), loan {money(LOAN)}, 30-year fixed at {RATE:.2f}%
• Monthly principal + interest: {money(PMT)}
• Total interest: {money(INTEREST)}
• Closing costs (assumption, 3%): {money(CLOSING)}
• Property tax at 0.888%/yr, flat value: {money(TAX_30)}
• Insurance (assumption, $2,400/yr): {money(INS_30)}
• Maintenance (1% rule): {money(MAINT_30)}
• Real 30-year total: {money(TOTAL)}
• Opportunity cost of {money(UPFRONT)} upfront at an assumed 7%/yr (not in total): {money(OPP_VALUE)}

SOURCES
• Mortgage rate: Freddie Mac Primary Mortgage Market Survey, 30-year fixed, week of {RATE_DATE:%B %-d, %Y}, via FRED (series MORTGAGE30US): https://fred.stlouisfed.org/series/MORTGAGE30US
• Property tax: NAHB, "Property Taxes by State, 2024" (analysis of 2024 American Community Survey): https://eyeonhousing.org/2025/11/property-taxes-by-state-2024/
• Insurance, closing-cost and maintenance figures are stated assumptions, not data. Get real quotes.

This video is for educational purposes only and is not financial advice.
"""


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(json.dumps(FACTS, indent=1, default=float))
    if only in ("all", "thumb"):
        still(thumbnail, os.path.join(OUT, "thumbnail.png"))
    if only in ("all", "video"):
        total, work = render(S, os.path.join(OUT, "v03_real_cost.mp4"), overlay=hud)
        write_srt(S, os.path.join(OUT, "captions.srt"))
        open(os.path.join(OUT, "description.txt"), "w").write(description(chapters(S)))
        print(f"rendered {total:.1f}s")
