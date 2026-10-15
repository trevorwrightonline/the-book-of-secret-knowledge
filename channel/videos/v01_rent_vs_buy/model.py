"""Rent vs buy simulation on real US data (monthly).

Buyer: buys a median-priced home (Census/HUD MSPUS) with 20% down, 30-yr fixed at
the Freddie Mac rate of the purchase month; pays P&I, property tax, insurance and
maintenance. Home value follows the S&P CoreLogic Case-Shiller US index.
Renter: rents an equivalent home; starting rent = price / price_to_rent / 12, then
grows with the CPI rent-of-primary-residence index. Invests the down payment and
closing costs in the S&P 500 (total return, Damodaran annual data).
Each month, whoever has the lower housing cost invests the difference.
At the end the buyer sells (6% selling costs) and repays the loan.
Simplifications (stated on screen): no income taxes, no mortgage-interest deduction,
no refinancing, no capital-gains tax.
"""
import os
import numpy as np
import pandas as pd
import xlrd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

TAX = 0.00888        # NAHB 2024 national effective rate, applied every year (assumption)
INSURE = 0.005       # assumption, % of value per year
MAINT = 0.01         # 1% rule
CLOSING = 0.03
SELLING = 0.06
DOWN = 0.20


def _fred(name):
    d = pd.read_csv(os.path.join(DATA, f"{name}.csv"), parse_dates=["observation_date"]).dropna()
    return d.set_index("observation_date").iloc[:, 0].astype(float)


def load():
    cs = _fred("CSUSHPINSA").resample("MS").first()
    rent = _fred("CUUR0000SEHA").resample("MS").first().interpolate()  # BLS skipped Oct 2025 (shutdown)
    rate = _fred("MORTGAGE30US").resample("MS").mean()
    price = _fred("MSPUS").resample("MS").ffill()
    sh = xlrd.open_workbook(os.path.join(DATA, "histretSP.xls")).sheet_by_name("Returns by year")
    spx = {}
    for r in range(sh.nrows):
        row = sh.row_values(r)
        if isinstance(row[0], float) and 1900 < row[0] < 2100 and isinstance(row[1], float):
            spx[int(row[0])] = row[1]
    return cs, rent, rate, price, spx


CS, RENT, RATE, PRICE, SPX = load()


def simulate(start, years=30, ptr=15.0, track=False):
    start = pd.Timestamp(start)
    months = pd.date_range(start, periods=years * 12, freq="MS")
    end = months[-1]
    p0 = PRICE[start]
    r_annual = RATE[start]
    r = r_annual / 100 / 12
    loan = p0 * (1 - DOWN)
    pmt = loan * r / (1 - (1 + r) ** -360)
    bal = loan
    rent0 = p0 / ptr / 12
    renter = p0 * (DOWN + CLOSING)
    buyer_port = 0.0
    hist = []
    for i, m in enumerate(months):
        g = (1 + SPX[m.year]) ** (1 / 12) - 1
        value = p0 * CS[m] / CS[start]
        rent = rent0 * RENT[m] / RENT[start]
        if i < 360:
            interest = bal * r
            bal -= pmt - interest
            pi = pmt
        else:
            pi = 0.0
        own_cost = pi + value * (TAX + INSURE + MAINT) / 12
        renter *= 1 + g
        buyer_port *= 1 + g
        diff = own_cost - rent
        if diff > 0:
            renter += diff
        else:
            buyer_port += -diff
        if track:
            hist.append(dict(month=m, value=value, balance=max(bal, 0), own_cost=own_cost, rent=rent,
                             buyer=value * (1 - SELLING) - max(bal, 0) + buyer_port, renter=renter))
    value_end = p0 * CS[end] / CS[start]
    buyer_nw = value_end * (1 - SELLING) - max(bal, 0) + buyer_port
    res = dict(start=start, end=end, p0=p0, rate=r_annual, pmt=pmt, rent0=rent0, value_end=value_end,
               buyer=buyer_nw, renter=renter, buyer_port=buyer_port)
    if track:
        res["hist"] = pd.DataFrame(hist).set_index("month")
    return res


if __name__ == "__main__":
    m = simulate("1996-01-01", track=True)
    print({k: (round(v) if isinstance(v, float) else v) for k, v in m.items() if k != "hist"})
    h = m["hist"]
    print(h.iloc[[0, 12, 60, 120, 240, 359]].round(0))
    for ptr in (10, 12, 15, 18, 21, 25):
        s = simulate("1996-01-01", ptr=ptr)
        print("ptr", ptr, "buyer", round(s["buyer"]), "renter", round(s["renter"]))
    print("10-yr holds, ptr 15")
    for y in range(1987, 2017):
        s = simulate(f"{y}-01-01", years=10)
        print(y, round(s["rate"], 2), round(s["buyer"]), round(s["renter"]), "BUY" if s["buyer"] > s["renter"] else "RENT")
