"""Dates, figures, and names in deck text that the user's source text does not contain.

Used by check_outline.py --prompt (dates and figures, as warnings) and evals/score.py
(dates, figures, and names). A date is sourced when each of its parts (month, day, year,
quarter, fiscal year) appears in the source, so "March 2027" is sourced by "March 3, 2027".
"""
from __future__ import annotations

import re
from typing import Iterable

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
_DAY = r"(?:\s+(\d{1,2})(?:st|nd|rd|th)?\b)?"
_YEAR = r"(?:,?\s+((?:19|20)\d{2})\b)?"
MONTH_DATE = re.compile(rf"\b({_MONTH}){_DAY}{_YEAR}")
YEAR = re.compile(r"(?<![\w$.,])((?:19|20)\d{2})(?![\w%])")
QUARTER = re.compile(r"\b(Q[1-4])\b", re.I)
FISCAL = re.compile(r"\bFY\s?'?(\d{2}|\d{4})\b", re.I)
NUMERIC_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b")
NUMBER = re.compile(r"(?<![\w.])-?\$?\d[\d,]*(?:\.\d+)?%?")
NAME = re.compile(r"\b(?:[A-Z][a-z]+(?:[A-Z][a-z]+)*|[A-Z]{2,})\b")
# Capitalized words a deck may use without the user saying them.
NAME_STOPLIST = {
    "Workday", "Confidential", "TODO", "TBD", "I", "OK", "AI", "FAQ", "Q", "FY", "YoY", "QoQ", "KPI", "KPIs",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
}


def _month(token: str) -> str:
    return token.strip(".").lower()[:3]


def date_parts(text: str) -> list[tuple[str, set[str]]]:
    """Each date-like string in text with the parts that must be sourced."""
    found: list[tuple[str, set[str]]] = []
    spans: list[tuple[int, int]] = []
    for m in MONTH_DATE.finditer(text):
        month, day, year = m.group(1), m.group(2), m.group(3)
        if month.startswith("May") and not (day or year):
            continue  # "may" is usually the verb
        if not (day or year) and text[m.end():m.end() + 1].isalpha():
            continue  # "Marketing", "Decision"
        parts = {_month(month)}
        if day:
            parts.add(f"{_month(month)} {int(day)}")
        if year:
            parts.add(year)
        found.append((m.group(0).strip(), parts))
        spans.append(m.span())
    for m in YEAR.finditer(text):
        if not any(a <= m.start() < b for a, b in spans):
            found.append((m.group(1), {m.group(1)}))
    for m in QUARTER.finditer(text):
        found.append((m.group(1), {m.group(1).lower()}))
    for m in FISCAL.finditer(text):
        found.append((m.group(0), {"fy" + m.group(1)[-2:]}))
    for m in NUMERIC_DATE.finditer(text):
        found.append((m.group(1), {m.group(1)}))
    return found


def source_date_parts(text: str) -> set[str]:
    out: set[str] = set()
    for _, parts in date_parts(text):
        out |= parts
    return out


def unsourced_dates(text: str, source: str) -> list[str]:
    have = source_date_parts(source)
    seen, out = set(), []
    for raw, parts in date_parts(text):
        if not parts <= have and raw not in seen:
            seen.add(raw)
            out.append(raw)
    return out


def _value(tok: str) -> float | None:
    try:
        return float(tok.strip("$%").replace(",", ""))
    except ValueError:
        return None


def figures(text: str) -> set[float]:
    """Numbers that carry a claim: decimals, percents, money, or 10 and up."""
    out = set()
    for tok in NUMBER.findall(text):
        value = _value(tok)
        if value is None:
            continue
        plain = tok.strip("-$%").replace(",", "")
        if "." in plain or "%" in tok or "$" in tok or abs(value) >= 10:
            out.add(value)
    return out


def all_figures(text: str) -> set[float]:
    out = set()
    for tok in NUMBER.findall(text):
        value = _value(tok)
        if value is not None:
            out |= {value, -value}
    return out


def unsourced_figures(text: str, source: str, allowed: Iterable[float] = ()) -> list[float]:
    """Figures in text not in source. Bare years are left to unsourced_dates."""
    have = all_figures(source) | set(allowed)
    return sorted(v for v in figures(text) - have if not (v.is_integer() and 1900 <= v <= 2099))


def names(segments: Iterable[str]) -> set[str]:
    """Capitalized words and acronyms that are not the first word of a sentence."""
    out = set()
    for seg in segments:
        for m in NAME.finditer(seg):
            before = seg[: m.start()].rstrip()
            if not before or before[-1] in ".:!?(\"'" or before.endswith(("- ", "-")):
                continue
            word = m.group(0)
            if word not in NAME_STOPLIST and not MONTH_DATE.fullmatch(word):
                out.add(word)
    return out


def unsourced_names(segments: Iterable[str], source: str) -> list[str]:
    words = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z']*", source)}
    singular = lambda w: w[:-1] if w.endswith("s") else w  # noqa: E731
    return sorted(n for n in names(segments) if n.lower() not in words and singular(n.lower()) not in words)
