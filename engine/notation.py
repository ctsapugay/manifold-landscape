"""Render raw expression source as readable mathematical notation.

This is a **display-only** transform for C-READABLE-OUTPUT (G12): it turns machine source a
person should not have to read — ``x**2 + 3*y**2``, ``10*(y - x)``, ``x*y - 8*z/3`` — into the
notation they recognise — ``x² + 3y²``, ``10(y − x)``, ``xy − 8z/3``. It never parses, evaluates,
or alters a mathematical *value*: it only reshapes how an already-computed expression string is
shown, so it cannot affect C-VERIFIED-MATH. The verified ``Quantity`` records keep their exact
source ``display``; notation is applied when composing the tutor's explanatory text.

Kept deliberately small and dependency-free (constraint C-LOCAL): a handful of ordered string
rewrites that cover the polynomial / trigonometric expressions the tool actually handles, with
honest fallbacks (``**`` → ``^``, ``*`` → ``·``) for anything unusual, so an unrecognised
expression is still made *more* readable, never corrupted.
"""

from __future__ import annotations

import re

# unicode superscripts for integer exponents
_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
        "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻"}

MINUS = "−"   # U+2212, the real minus sign (not a hyphen)
CDOT = "·"    # U+00B7, multiplication dot


def _superscript(digits: str) -> str:
    return "".join(_SUP.get(c, c) for c in digits)


def to_notation(src: str) -> str:
    """Return ``src`` rewritten as readable notation. Display-only; value-preserving."""
    if src is None:
        return ""
    s = str(src)

    # 1. integer powers -> unicode superscripts:  x**2 -> x²,  z**10 -> z¹⁰
    s = re.sub(r"\*\*\s*(\d+)", lambda m: _superscript(m.group(1)), s)
    # any remaining exponent (symbolic / fractional) -> a plain caret
    s = s.replace("**", "^")

    # 2. multiplication:
    #    - a numeric coefficient touching a name or a bracket is written implicitly:
    #        3*y -> 3y,   10*(y - x) -> 10(y - x),   8*z -> 8z
    s = re.sub(r"(?<=\d)\s*\*\s*(?=[A-Za-z(])", "", s)
    #    - everything else that multiplies becomes a centred dot:  x*y -> x·y
    s = re.sub(r"\s*\*\s*", CDOT, s)

    # 3. real minus sign for subtraction and leading negatives (cosmetic, value-preserving)
    s = re.sub(r"(?<=[\w).²³¹⁰⁴⁵⁶⁷⁸⁹])\s*-\s*(?=[\w(])", f" {MINUS} ", s)

    def _lead_minus(m):
        d = m.group(1)
        # a unary minus hugs its operand at the start of the string or just after "(",
        # but keeps a space after "," or "=" so a tuple/equation stays readable
        return (d + MINUS) if d in ("(", "") else (d + " " + MINUS)

    s = re.sub(r"(^|[(,=])\s*-\s*", _lead_minus, s)

    # 4. tidy doubled spaces
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def vec_notation(parts) -> str:
    """Render a list/tuple of component sources as a notation vector, e.g. (−y, x)."""
    return "(" + ", ".join(to_notation(p) for p in parts) + ")"


def matrix_notation(rows) -> str:
    """Render a numeric matrix compactly as bracketed rows, e.g. [[2, 1], [1, 2]]."""
    def fmt(v):
        f = float(v)
        s = str(int(round(f))) if abs(f - round(f)) < 1e-9 else f"{f:.3g}"
        return s.replace("-", MINUS)
    return "[" + "; ".join("[" + ", ".join(fmt(v) for v in row) + "]" for row in rows) + "]"
