"""Spell numbers out for narration so the TTS never misreads them."""
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen " \
       "fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _lt1000(n):
    out = []
    if n >= 100:
        out.append(ONES[n // 100] + " hundred")
        n %= 100
    if n >= 20:
        out.append(TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else ""))
    elif n or not out:
        out.append(ONES[n])
    return " ".join(out)


def words(n):
    n = int(round(n))
    if n == 0:
        return "zero"
    parts = []
    for div, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand"), (1, "")):
        if n >= div:
            parts.append((_lt1000(n // div) + " " + name).strip())
            n %= div
    return " ".join(parts)


def dollars(v, round_to=None):
    """'$478,213' -> 'four hundred seventy-eight thousand dollars' (rounded)."""
    if round_to is None:
        round_to = 1000 if v >= 100_000 else (100 if v >= 10_000 else (10 if v >= 1000 else 1))
    return words(round(v / round_to) * round_to) + " dollars"


def pct(v):
    """7.4 -> 'seven point four percent'."""
    s = f"{v:g}"
    if "." in s:
        a, b = s.split(".")
        return f"{words(int(a))} point {' '.join(ONES[int(c)] for c in b)} percent"
    return f"{words(int(s))} percent"
