"""Minimal WCAG contrast verification for the v3 color-token text and control pairs."""
from __future__ import annotations

TOKENS = {
    "surface": "#ffffff", "ink": "#172124", "muted": "#526267", "teal": "#0c6b68",
    "teal_dark": "#075451", "teal_soft": "#e5f2f0", "amber": "#8a4f00", "amber_soft": "#fff4dd",
    "withheld": "#3c5665", "withheld_soft": "#eaf0f4", "danger": "#8c1d18", "danger_soft": "#fdecea",
    "control_border": "#738682",
}
PAIRS = {
    "body ink on surface": ("ink", "surface", 4.5),
    "body muted on surface": ("muted", "surface", 4.5),
    "teal text on soft teal": ("teal_dark", "teal_soft", 4.5),
    "amber text on soft amber": ("amber", "amber_soft", 4.5),
    "withheld text on soft withheld": ("withheld", "withheld_soft", 4.5),
    "danger text on soft danger": ("danger", "danger_soft", 4.5),
    "form border on surface": ("control_border", "surface", 3.0),
    "focus ring on surface": ("teal", "surface", 3.0),
}


def _luminance(hex_value: str) -> float:
    rgb = [int(hex_value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in rgb]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def ratio(left: str, right: str) -> float:
    first, second = sorted((_luminance(TOKENS[left]), _luminance(TOKENS[right])), reverse=True)
    return (first + 0.05) / (second + 0.05)


if __name__ == "__main__":
    failed = []
    for name, (left, right, minimum) in PAIRS.items():
        value = ratio(left, right)
        print(f"{name}: {value:.2f}:1 (minimum {minimum:.1f}:1)")
        if value < minimum:
            failed.append(name)
    if failed:
        raise SystemExit("contrast failures: " + ", ".join(failed))
