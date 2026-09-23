"""Console presentation of an analysis result dictionary."""

from analysis import round_for_display

FEATURE_LABELS = {
    "pitch": "Pitch (Hz)",
    "energy": "Energy",
    "speech_rate": "Speech rate (wpm)",
    "pause_ratio": "Pause ratio",
    "background_noise": "Background noise",
    "signal_quality": "Signal quality",
}
DECIMALS = {
    "pitch": 1,
    "energy": 2,
    "speech_rate": 1,
    "pause_ratio": 2,
    "background_noise": 2,
    "signal_quality": 2,
}
# Change is shown as a percentage for these features and as a difference for
# the 0-1 ratios, matching the units the style rules use.
PERCENT_CHANGE = ("pitch", "speech_rate")
WIDTH = 74


def format_number(value, decimals):
    return "-" if value is None else f"{value:.{decimals}f}"


def format_change(feature, comparison):
    entry = comparison.get(feature)
    if not entry or entry["difference"] is None:
        return ""
    if feature in PERCENT_CHANGE and entry["percent"] is not None:
        return f"{round_for_display(entry['percent'], 1):+.1f}%"
    return f"{round_for_display(entry['difference'], 2):+.2f}"


def format_feature_table(summary, comparison):
    """Return one table row per feature: summary statistics plus the change from usual."""
    header = f"{'Feature':<19}{'Mean':>8}{'Min':>8}{'Max':>8}{'Stdev':>8}{'Usual':>8}{'Change':>9}"
    lines = [header, "-" * len(header)]
    for feature, label in FEATURE_LABELS.items():
        decimals = DECIMALS[feature]
        stats = summary.get(feature)
        entry = comparison.get(feature)
        usual = format_number(entry["usual"], decimals) if entry else ""
        if stats is None:
            lines.append(f"{label:<19}{'no usable values':>32}{usual:>8}")
            continue
        cells = "".join(
            f"{format_number(stats[key], decimals):>8}" for key in ("mean", "min", "max", "stdev")
        )
        lines.append(f"{label:<19}{cells}{usual:>8}{format_change(feature, comparison):>9}")
    return "\n".join(lines)


def format_window_notes(result):
    """List the rejected and flagged windows with their reasons."""
    lines = []
    if result["rejections"]:
        lines.append("Rejected windows")
        for entry in result["rejections"]:
            lines.append(f"  t={entry['timestamp']!s:<4} " + "; ".join(entry["reasons"]))
    if result["warnings"]:
        lines.append("Flagged windows (still used)")
        for entry in result["warnings"]:
            lines.append(f"  t={entry['timestamp']!s:<4} " + "; ".join(entry["warnings"]))
    return "\n".join(lines)


def format_assessment(heading, assessment):
    label = assessment["label"].upper()
    if assessment.get("score") is not None:
        label += f" ({assessment['score']}/100)"
    lines = [f"{heading}: {label}"]
    lines.extend(f"  - {reason}" for reason in assessment["reasons"])
    return "\n".join(lines)


def format_report(result):
    """Return the complete report for one session as a string."""
    counts = result["windows"]
    parts = [
        "=" * WIDTH,
        f"{result['session_title']}  |  speaker {result['speaker_id']}",
        "-" * WIDTH,
        (
            f"Windows: {counts['total']} total, {counts['usable']} usable, "
            f"{counts['rejected']} rejected, {counts['flagged']} flagged"
        ),
        "",
        format_feature_table(result["summary"], result["comparison"]),
    ]
    notes = format_window_notes(result)
    if notes:
        parts += ["", notes]
    parts += [
        "",
        format_assessment("Speaking style", result["style"]),
        format_assessment("Recording quality", result["quality"]),
    ]
    return "\n".join(parts)


def print_report(result):
    print(format_report(result))
    print()
