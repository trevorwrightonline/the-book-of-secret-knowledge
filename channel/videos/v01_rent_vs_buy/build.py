"""Video 1: Is Renting Really "Throwing Money Away"? I Ran 30 Years of Numbers.

Run from channel/:  python3 videos/v01_rent_vs_buy/build.py [thumb|video|all]
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

OUT = os.path.join(CH, "out", "v01_rent_vs_buy")
os.makedirs(OUT, exist_ok=True)

START = "1996-01-01"
PTR = 15.0
R = M.simulate(START, ptr=PTR, track=True)
H = R["hist"]
P0, RATE0 = R["p0"], R["rate"]
UPFRONT = P0 * (M.DOWN + M.CLOSING)
GAP = R["renter"] - R["buyer"]

# break-even price-to-rent ratio (bisection)
lo, hi = 8.0, 25.0
for _ in range(40):
    mid = (lo + hi) / 2
    s = M.simulate(START, ptr=mid)
    lo, hi = (mid, hi) if s["buyer"] > s["renter"] else (lo, mid)
BREAKEVEN = lo
PTR_GRID = np.arange(10, 25.5, 0.5)
PTR_RES = [M.simulate(START, ptr=p) for p in PTR_GRID]

# money that's gone for good
r = RATE0 / 100 / 12
bal, INTEREST = P0 * (1 - M.DOWN), 0.0
for _ in range(360):
    it = bal * r
    INTEREST += it
    bal -= R["pmt"] - it
CARRY = float((H.value * (M.TAX + M.INSURE + M.MAINT) / 12).sum())
CLOSE_SELL = P0 * M.CLOSING + R["value_end"] * M.SELLING
BUYER_GONE = INTEREST + CARRY + CLOSE_SELL
RENT_GONE = float(H.rent.sum())
CROSS_COST = H[H.own_cost < H.rent].index.min()

# lead changes in net worth
lead = (H.buyer > H.renter)
BUY_LEAD_START = lead[lead].index.min()
BUY_LEAD_END = lead[lead].index.max()

# 10-year holds by start year
SWEEP = [(y, M.simulate(f"{y}-01-01", years=10, ptr=PTR)) for y in range(1987, 2017)]
BUY_WINS = [y for y, s in SWEEP if s["buyer"] > s["renter"]]

FACTS = dict(p0=P0, rate0=RATE0, pmt=R["pmt"], rent0=R["rent0"], own0=float(H.own_cost.iloc[0]),
             value_end=R["value_end"], buyer=R["buyer"], renter=R["renter"], gap=GAP, breakeven=BREAKEVEN,
             interest=INTEREST, carry=CARRY, close_sell=CLOSE_SELL, buyer_gone=BUYER_GONE, rent_gone=RENT_GONE,
             rent_end=float(H.rent.iloc[-1]), own_end=float(H.own_cost.iloc[-1]), cost_cross=str(CROSS_COST.date()),
             buy_lead=[str(BUY_LEAD_START.date()), str(BUY_LEAD_END.date())], buy_win_years=BUY_WINS)
json.dump(FACTS, open(os.path.join(OUT, "facts.json"), "w"), indent=2, default=float)

SRC = ("Sources: Census/HUD median sales price (MSPUS), S&P CoreLogic Case-Shiller US index, BLS CPI rent, "
       "Freddie Mac PMMS via FRED · S&P 500 total return: Damodaran (NYU)")
ASSUME = f"Assumptions: price-to-rent {PTR:g} at start · tax 0.89% · insurance 0.5% · maintenance 1% of value/yr · 3% closing · 6% selling · no income taxes"


def header(fig, s):
    txt(fig, 0.04, 0.93, s.upper(), size=22, color=C["muted"], ha="left")


def prog(c, frac=0.85):
    return min(1.0, c.beat_t / max(0.1, c.beat_d * frac))


def style(ax, money_axis=True):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", color=C["grid"])
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=16)
    if money_axis:
        ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:,.0f}k")


# ---------------- scenes ----------------
def d_hook(fig, c):
    txt(fig, 0.5, 0.72, "“Renting is throwing", size=80, alpha=c.bp if c.beat == 0 else 1)
    txt(fig, 0.5, 0.6, "money away.”", size=80, alpha=c.bp if c.beat == 0 else 1)
    if c.beat >= 1:
        txt(fig, 0.5, 0.4, "Two people · January 1996 · 30 years of real data", size=34, weight="medium",
            color=C["muted"], alpha=c.bp if c.beat == 1 else 1)
    if c.beat >= 2:
        txt(fig, 0.5, 0.24, f"One ends up {money(abs(GAP))} richer", size=56, color=C["amber"],
            alpha=c.bp)


def d_meet(fig, c):
    header(fig, "Meet the buyer and the renter")
    a0 = c.bp if c.beat == 0 else 1
    box(fig, 0.05, 0.2, 0.42, 0.62, C["panel"], alpha=a0)
    txt(fig, 0.26, 0.75, "THE BUYER", size=34, color=C["red"], alpha=a0)
    for i, s in enumerate([f"Median home: {money(P0)}", f"20% down + 3% closing", f"30-yr fixed at {RATE0:.2f}%",
                           f"Payment: {money(R['pmt'])}/mo (P&I)"]):
        txt(fig, 0.08, 0.63 - i * 0.09, s, size=28, weight="medium", ha="left", alpha=a0)
    if c.beat >= 1:
        a1 = c.bp if c.beat == 1 else 1
        box(fig, 0.53, 0.2, 0.42, 0.62, C["panel"], alpha=a1)
        txt(fig, 0.74, 0.75, "THE RENTER", size=34, color=C["teal"], alpha=a1)
        for i, s in enumerate([f"Rents the same kind of home", f"Rent: {money(R['rent0'])}/mo",
                               f"Invests {money(UPFRONT)} upfront", "in an S&P 500 index fund"]):
            txt(fig, 0.56, 0.63 - i * 0.09, s, size=28, weight="medium", ha="left", alpha=a1)
        badge(fig, 0.56, 0.25, f" ASSUMPTION: HOME PRICE = {PTR:g}× A YEAR'S RENT ", size=15)
    source(fig, SRC)


def d_rules(fig, c):
    header(fig, "The rules")
    rules = ["Each month, add up every housing cost",
             "Owner: mortgage + property tax + insurance + maintenance",
             "Renter: rent",
             "Whoever pays less invests the difference",
             "After 30 years, the buyer sells (6% costs). Compare net worth."]
    n = 3 if c.beat == 0 else 5
    for i, s in enumerate(rules[:n]):
        a = ease(c.beat_t / 0.4 - (i if c.beat == 0 else i - 3) * 0.8) if (c.beat == 0 or i >= 3) else 1
        txt(fig, 0.08, 0.76 - i * 0.12, f"{i + 1}.  {s}", size=34, weight="medium", ha="left", alpha=a)
    source(fig, ASSUME)


def d_costs(fig, c):
    header(fig, "Monthly housing cost: owning vs renting")
    ax = fig.add_axes([0.08, 0.15, 0.86, 0.66])
    p = prog(c) if c.beat == 0 else 1
    k = max(2, int(len(H) * p))
    ax.plot(H.index[:k], H.own_cost.iloc[:k], color=C["red"], lw=4, label="Owner")
    ax.plot(H.index[:k], H.rent.iloc[:k], color=C["teal"], lw=4, label="Renter")
    ax.set_xlim(H.index[0], H.index[-1]); ax.set_ylim(0, max(H.own_cost.max(), H.rent.max()) * 1.15)
    style(ax)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.legend(loc="upper left", frameon=False, fontsize=22, labelcolor=C["text"])
    if c.beat >= 1:
        ax.axvline(CROSS_COST, color=C["amber"], ls="--", lw=3, alpha=c.bp if c.beat == 1 else 1)
        ax.text(CROSS_COST, ax.get_ylim()[1] * 0.93, f"  {CROSS_COST.year}: rent passes owning",
                color=C["amber"], fontsize=22, fontweight="bold", alpha=c.bp if c.beat == 1 else 1)
    source(fig, SRC)


def d_race(fig, c):
    header(fig, "Net worth: buyer vs renter")
    ax = fig.add_axes([0.08, 0.15, 0.86, 0.66])
    p = prog(c, 0.9) if c.beat == 0 else 1
    k = max(2, int(len(H) * p))
    ax.plot(H.index[:k], H.buyer.iloc[:k], color=C["red"], lw=4, label="Buyer (home equity after selling costs + investments)")
    ax.plot(H.index[:k], H.renter.iloc[:k], color=C["teal"], lw=4, label="Renter (investments)")
    ax.set_xlim(H.index[0], H.index[-1]); ax.set_ylim(0, max(H.buyer.max(), H.renter.max()) * 1.12)
    style(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=20, labelcolor=C["text"])
    if c.beat >= 1 or p >= 1:
        ax.annotate(money(R["renter"]), (H.index[-1], R["renter"]), xytext=(-210, 8), textcoords="offset points",
                    color=C["teal"], fontsize=28, fontweight="bold")
        ax.annotate(money(R["buyer"]), (H.index[-1], R["buyer"]), xytext=(-60, -55), textcoords="offset points",
                    color=C["red"], fontsize=28, fontweight="bold")
    if c.beat >= 1:
        ax.axvspan(BUY_LEAD_START, BUY_LEAD_END, color=C["red"], alpha=0.12 * (c.bp if c.beat == 1 else 1))
        ax.text(BUY_LEAD_START, ax.get_ylim()[1] * 0.62, " Housing boom:\n buyer ahead", color=C["red"],
                fontsize=20, fontweight="bold", alpha=c.bp if c.beat == 1 else 1)
    source(fig, ASSUME)


def d_gone(fig, c):
    header(fig, "Money that's gone for good, over 30 years")
    mx = max(RENT_GONE, BUYER_GONE)
    p = c.bp
    # renter
    txt(fig, 0.06, 0.66, "Renter", size=34, ha="left", color=C["teal"])
    box(fig, 0.22, 0.61, 0.6 * RENT_GONE / mx * (p if c.beat == 0 else 1), 0.1, C["teal"])
    txt(fig, 0.23 + 0.6 * RENT_GONE / mx * (p if c.beat == 0 else 1), 0.66, money(RENT_GONE * (p if c.beat == 0 else 1)),
        size=30, ha="left")
    txt(fig, 0.22, 0.56, "Rent", size=20, weight="medium", color=C["muted"], ha="left")
    if c.beat >= 1:
        txt(fig, 0.06, 0.4, "Buyer", size=34, ha="left", color=C["red"])
        x = 0.22
        for name, v, col in (("Interest", INTEREST, C["red"]), ("Tax, insurance, upkeep", CARRY, C["amber"]),
                             ("Closing + selling", CLOSE_SELL, C["gray"])):
            w = 0.6 * v / mx * c.bp
            box(fig, x, 0.35, w, 0.1, col)
            txt(fig, x + w / 2, 0.29, name, size=17, weight="medium", color=C["muted"])
            x += w
        txt(fig, x + 0.01, 0.4, money(BUYER_GONE * c.bp), size=30, ha="left")
    if c.beat >= 2:
        txt(fig, 0.5, 0.14, "Both “throw money away.” The question is who builds more on the side.",
            size=30, color=C["amber"], alpha=c.bp)


def d_ratio(fig, c):
    header(fig, "The one number that decides it")
    if c.beat == 0:
        txt(fig, 0.5, 0.62, "PRICE-TO-RENT RATIO", size=80, color=C["amber"], alpha=c.bp)
        txt(fig, 0.5, 0.45, "home price  ÷  one year's rent for a similar home", size=40, weight="medium", alpha=c.bp)
        txt(fig, 0.5, 0.33, "$300,000 ÷ ($1,500 × 12) = 16.7", size=34, weight="medium", color=C["muted"], alpha=c.bp)
        return
    ax = fig.add_axes([0.08, 0.15, 0.86, 0.66])
    p = prog(c) if c.beat == 1 else 1
    k = max(2, int(len(PTR_GRID) * p))
    ax.plot(PTR_GRID[:k], [s["buyer"] for s in PTR_RES[:k]], color=C["red"], lw=4, label="Buyer")
    ax.plot(PTR_GRID[:k], [s["renter"] for s in PTR_RES[:k]], color=C["teal"], lw=4, label="Renter")
    ax.set_xlim(PTR_GRID[0], PTR_GRID[-1])
    ax.set_ylim(0, max(max(s["buyer"], s["renter"]) for s in PTR_RES) * 1.1)
    style(ax)
    ax.set_xlabel("Price-to-rent ratio in 1996", fontsize=20)
    ax.set_ylabel("Net worth after 30 years", fontsize=18)
    ax.legend(loc="upper center", frameon=False, fontsize=22, labelcolor=C["text"], ncol=2)
    if c.beat == 2:
        ax.axvline(BREAKEVEN, color=C["amber"], ls="--", lw=3, alpha=c.bp)
        ax.text(BREAKEVEN + 0.2, ax.get_ylim()[1] * 0.8, f"Break-even ≈ {BREAKEVEN:.0f}", color=C["amber"],
                fontsize=26, fontweight="bold", alpha=c.bp)
        ax.text(10.3, ax.get_ylim()[1] * 0.05, "← buying wins", color=C["red"], fontsize=22, fontweight="bold", alpha=c.bp)
        ax.text(24.7, ax.get_ylim()[1] * 0.05, "renting + investing wins →", color=C["teal"], fontsize=22,
                fontweight="bold", ha="right", alpha=c.bp)
    source(fig, ASSUME.replace(f"price-to-rent {PTR:g} at start · ", ""))


def d_timing(fig, c):
    header(fig, "Does WHEN you buy matter? 10-year holds")
    ax = fig.add_axes([0.08, 0.17, 0.86, 0.62])
    p = prog(c) if c.beat == 0 else 1
    k = max(1, int(len(SWEEP) * p))
    ys = [y for y, _ in SWEEP][:k]
    diff = [s["buyer"] - s["renter"] for _, s in SWEEP][:k]
    ax.bar(ys, diff, color=[C["red"] if d > 0 else C["teal"] for d in diff], width=0.75)
    ax.axhline(0, color=C["muted"], lw=1.5)
    ax.set_xlim(1986.3, 2016.7)
    allv = [s["buyer"] - s["renter"] for _, s in SWEEP]
    ax.set_ylim(min(allv) * 1.2, max(allv) * 1.35)
    style(ax)
    ax.set_xlabel("Year you bought (held 10 years)", fontsize=20)
    ax.set_ylabel("Buyer minus renter", fontsize=18)
    ax.text(1987, max(allv) * 1.15, "▲ buying won", color=C["red"], fontsize=22, fontweight="bold")
    ax.text(1987, min(allv) * 1.1, "▼ renting won", color=C["teal"], fontsize=22, fontweight="bold")
    if c.beat >= 1:
        txt(fig, 0.5, 0.86, "Same ratio every year. Only rates, prices and markets change.", size=28,
            weight="medium", color=C["amber"], alpha=c.bp)
    source(fig, ASSUME)


def d_rule(fig, c):
    header(fig, "How to use this for YOUR city")
    rows = [("Below ~13", "Buying held up well in this test", C["red"]),
            ("13 to ~18", "Toss-up: rates and how long you stay decide", C["amber"]),
            ("Above ~18", "Renting + investing usually came out ahead", C["teal"])]
    for i, (k, v, col) in enumerate(rows[: c.beat + 1]):
        y = 0.68 - i * 0.16
        a = c.bp if i == c.beat else 1
        box(fig, 0.06, y - 0.06, 0.88, 0.12, C["panel"], alpha=a)
        txt(fig, 0.09, y, k, size=40, color=col, ha="left", alpha=a)
        txt(fig, 0.36, y, v, size=32, weight="medium", ha="left", alpha=a)
    badge(fig, 0.06, 0.12, " BASED ON ONE 30-YEAR US PATH · NOT A FORECAST · NOT FINANCIAL ADVICE ", size=15)


def d_catch(fig, c):
    header(fig, "The catch")
    items = ["The renter must invest every spare dollar, every month",
             "…and hold through the 2000, 2008 and 2020 crashes",
             "Owning is forced savings, stability, and control",
             "Taxes, refinancing and moving would change the numbers"]
    for i, s in enumerate(items[: c.beat + 1]):
        y = 0.74 - i * 0.14
        a = c.bp if i == c.beat else 1
        txt(fig, 0.08, y, "•  " + s, size=36, weight="medium", ha="left", alpha=a)


def d_cta(fig, c):
    if c.beat == 0:
        txt(fig, 0.5, 0.62, "What's YOUR city's ratio?", size=76, alpha=c.bp)
        txt(fig, 0.5, 0.47, "Comment: city + home price + rent for a similar place", size=36, weight="medium",
            color=C["muted"], alpha=c.bp)
    else:
        txt(fig, 0.5, 0.64, "NEXT", size=30, color=C["muted"])
        txt(fig, 0.5, 0.53, "How long it takes to save a down payment,", size=54, color=C["teal"], alpha=c.bp)
        txt(fig, 0.5, 0.44, "in every major US city", size=54, color=C["teal"], alpha=c.bp)
        txt(fig, 0.5, 0.1, "Educational only. Not financial advice. Full method, code & sources in the description.",
            size=20, weight="normal", color=C["muted"])


renter_ahead_after = BUY_LEAD_END.year
S = [
    Scene(chapter="Intro", draw=d_hook, beats=[
        "Renting is throwing money away. You've heard it a thousand times.",
        "So I tested it. Two people, starting in January nineteen ninety-six, with a mortgage rate of about seven "
        "percent, almost exactly what it is today. One buys a home. The other rents, and invests the difference.",
        f"Thirty years later, one of them is about {dollars(abs(GAP))} richer. And the reason has almost nothing "
        "to do with who threw money away.",
    ]),
    Scene(chapter="The buyer and the renter", draw=d_meet, beats=[
        f"The buyer pays {dollars(P0)}, the median price of a home sold in the US at the time. Twenty percent down, "
        f"plus closing costs, and a thirty-year fixed mortgage at seven percent. That's a payment of about "
        f"{dollars(R['pmt'])} a month.",
        f"The renter rents the same kind of home for about {dollars(R['rent0'])} a month. That assumes the home's "
        f"price was {words(PTR)} times a year's rent, and we'll see how much that one assumption matters. Instead "
        f"of a down payment, the renter puts the same {dollars(UPFRONT)} into an S&P five hundred index fund.",
    ]),
    Scene(chapter="The rules", draw=d_rules, beats=[
        "Here are the rules. Every month, we add up every housing cost. For the owner, that's the mortgage, "
        "property tax, insurance, and maintenance. For the renter, it's rent.",
        "Whoever pays less that month invests the difference in the same index fund. After thirty years, the buyer "
        "sells the house, pays six percent in selling costs, and we compare what each of them has.",
    ]),
    Scene(chapter="Monthly costs", draw=d_costs, beats=[
        f"At the start, owning costs more. About {dollars(H.own_cost.iloc[0])} a month all-in, against "
        f"{dollars(R['rent0'])} in rent. So the renter invests the gap, every single month.",
        f"But rent keeps rising, while the mortgage payment never changes. By {words(CROSS_COST.year // 100)} "
        f"{words(CROSS_COST.year % 100)}, rent passes the total cost of owning, and from then on, it's the buyer "
        "who invests the difference.",
    ]),
    Scene(chapter="The net worth race", draw=d_race, beats=[
        "Now watch their net worth. The renter jumps ahead early, because the stock market of the late nineties "
        "was on fire. Then the housing boom kicks in.",
        f"For about a decade, through the bubble years, the buyer is ahead. But after {words(renter_ahead_after // 100)} "
        f"{words(renter_ahead_after % 100)}, the renter's investments pull away. After thirty years, the renter "
        f"has about {dollars(R['renter'])}. The buyer has about {dollars(R['buyer'])}, mostly in the house.",
    ]),
    Scene(chapter="Who threw money away?", draw=d_gone, beats=[
        f"So did the buyer avoid throwing money away? Over thirty years, the renter paid about "
        f"{dollars(RENT_GONE)} in rent. That money's gone.",
        f"But the buyer also paid money they'll never get back. About {dollars(INTEREST)} in interest, "
        f"{dollars(CARRY)} in property tax, insurance and maintenance, and {dollars(CLOSE_SELL)} in closing and "
        f"selling costs. That's about {dollars(BUYER_GONE)}.",
        "Both of them threw money away. Almost the same amount. The real question is who built more wealth on the "
        "side.",
    ]),
    Scene(chapter="The one number that decides it", draw=d_ratio, beats=[
        "And that comes down to one number, the price-to-rent ratio. It's the price of a home, divided by one "
        "year's rent for a similar home.",
        "Here's what happens when I rerun the same thirty years with different ratios. When homes are cheap "
        "compared to rent, buying wins easily. When they're expensive compared to rent, renting and investing "
        "wins.",
        f"In this test, the break-even point was a ratio of about {words(round(BREAKEVEN))}.",
    ]),
    Scene(chapter="Does timing matter?", draw=d_timing, beats=[
        "Timing matters too. Here, I kept the ratio the same, and only changed the year you bought, holding for ten "
        "years each time.",
        "Buy in the mid-nineties, or in the years after the two thousand eight crash, and buying won. Buy in the "
        "late eighties, or in the run-up to two thousand eight, and renting won. Same rules. Different years.",
    ]),
    Scene(chapter="Use it for your city", draw=d_rule, anim=0.8, beats=[
        "So here's how to use this. Find a home you'd buy, and the rent for a similar one nearby. Divide the price "
        "by a year of rent. If the ratio is below about thirteen, buying held up well in this test.",
        "Between thirteen and about eighteen, it's a toss-up, and your interest rate and how long you'll stay "
        "decide it.",
        "And above about eighteen, renting and investing usually came out ahead. Remember, this is one historical "
        "path, not a forecast.",
    ]),
    Scene(chapter="The catch", draw=d_catch, anim=0.7, beats=[
        "Now, the catch. The renter only wins if they actually invest every spare dollar, every month, for thirty "
        "years.",
        "And they have to hold on through the crashes of two thousand, two thousand eight, and twenty twenty, "
        "without selling.",
        "Owning has real benefits too: forced savings, stability, and nobody can raise your rent or ask you to "
        "leave.",
        "And I've left out taxes, refinancing, and moving, which would all change the numbers. The code and the "
        "full method are in the description, so you can check my work.",
    ]),
    Scene(chapter="Your turn", draw=d_cta, beats=[
        "So, renting isn't throwing money away, and buying isn't automatically the smart move. It depends on the "
        "numbers where you live. Comment your city, a typical home price, and the rent for a similar place, and "
        "I'll tell you your ratio.",
        "Next, I'm ranking how long it takes to save a down payment in every major US city. Subscribe so you "
        "don't miss it. This is for education, not financial advice. See you in the next one.",
    ]),
]


def thumbnail(fig):
    ax = fig.add_axes([0.52, 0.12, 0.44, 0.7])
    ax.plot(H.index, H.buyer, color=C["red"], lw=10)
    ax.plot(H.index, H.renter, color=C["teal"], lw=10)
    ax.set_axis_off()
    txt(fig, 0.05, 0.8, "RENTING =", size=80, ha="left")
    txt(fig, 0.05, 0.62, "THROWING", size=80, ha="left")
    txt(fig, 0.05, 0.44, "MONEY AWAY?", size=80, ha="left")
    txt(fig, 0.05, 0.2, " 30 YEARS OF DATA ", size=46, ha="left", color=C["bg"],
        bbox=dict(boxstyle="round,pad=0.3", facecolor=C["amber"], edgecolor="none"))


def description(chaps):
    return f"""Is renting really throwing money away? I ran 30 years of real US data: one person buys a median-priced home in January 1996 at a 7% mortgage rate, the other rents and invests the difference.

Comment your city, a typical home price and the rent for a similar place, and I'll work out your price-to-rent ratio.

CHAPTERS
{chr(10).join(chaps)}

RESULTS (start Jan 1996, price-to-rent ratio {PTR:g})
• Buyer: {money(P0)} home, 20% down, {RATE0:.2f}% 30-yr fixed; payment {money(R['pmt'])}/mo
• Renter: starting rent {money(R['rent0'])}/mo, invests {money(UPFRONT)} upfront in the S&P 500
• After 30 years: renter {money(R['renter'])}, buyer {money(R['buyer'])} (home sold, 6% costs, plus investments)
• Money gone for good: rent {money(RENT_GONE)} vs buyer interest + tax/insurance/maintenance + closing/selling {money(BUYER_GONE)}
• Break-even price-to-rent ratio in this test: about {BREAKEVEN:.1f}

METHOD & ASSUMPTIONS
Monthly simulation. Home value follows the Case-Shiller US national index; rent follows CPI rent of primary residence; mortgage rate is the Freddie Mac average for the purchase month. Property tax 0.89%/yr (NAHB 2024 national rate, applied throughout), insurance 0.5%/yr and maintenance 1%/yr of home value, 3% closing costs, 6% selling costs. Whoever has lower monthly housing costs invests the difference in the S&P 500 (total return, annual data spread evenly across months). Ignores income taxes, the mortgage-interest deduction, refinancing and capital-gains tax. One historical path, not a forecast.

SOURCES
• Median sales price of houses sold (MSPUS), Census/HUD via FRED: https://fred.stlouisfed.org/series/MSPUS
• S&P CoreLogic Case-Shiller U.S. National Home Price Index (CSUSHPINSA) via FRED: https://fred.stlouisfed.org/series/CSUSHPINSA
• CPI: Rent of primary residence, U.S. city average (CUUR0000SEHA), BLS via FRED: https://fred.stlouisfed.org/series/CUUR0000SEHA (Oct 2025 not published; interpolated)
• 30-year fixed mortgage rate (MORTGAGE30US), Freddie Mac via FRED: https://fred.stlouisfed.org/series/MORTGAGE30US
• S&P 500 annual total returns: Aswath Damodaran, NYU Stern: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html
• Property tax rate: NAHB analysis of the 2024 ACS: https://eyeonhousing.org/2025/11/property-taxes-by-state-2024/

This video is for educational purposes only and is not financial advice.
"""


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(json.dumps(FACTS, indent=1, default=float))
    if only in ("all", "thumb"):
        still(thumbnail, os.path.join(OUT, "thumbnail.png"))
    if only in ("all", "video"):
        total, work = render(S, os.path.join(OUT, "v01_rent_vs_buy.mp4"))
        write_srt(S, os.path.join(OUT, "captions.srt"))
        open(os.path.join(OUT, "description.txt"), "w").write(description(chapters(S)))
        print(f"rendered {total:.1f}s")
