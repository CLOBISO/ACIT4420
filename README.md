# Podcast Voice and Recording Analyzer

**ACIT4420 Programming Assignment I, Option B**

- **Student name:** Charlyn Joy Lacbayo Obiso
- **Student number:** 410318

## Description

A podcast company uses a separate tool to extract numerical features from short speech windows. This program works on those features only; it never sees the audio or what was said. It:

1. builds a speaker and their usual acoustic profile;
2. groups the observation windows into a recording session;
3. validates every window and rejects or flags bad ones, with reasons;
4. summarises all six features (mean, minimum, maximum and standard deviation);
5. compares the session with the speaker's usual profile;
6. describes the speaking style as **consistent**, **energetic**, **deliberate**, **temporarily varied**, **noise affected** or **insufficient data**;
7. scores overall recording quality from 0 to 100 and explains the score; and
8. returns everything as one dictionary and prints a readable console report.

The data comes from the instructor-supplied `data_generator.py`, which is included unchanged.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Entry point. Runs all seven scenarios and prints a report for each. |
| `models.py` | Domain classes: `AcousticProfile`, `Speaker`, `AcousticWindow`, `RecordingSession`. |
| `analysis.py` | Validation rules, calculations, the assessment classes and `SessionAnalyzer`. |
| `report.py` | Functions that turn a result dictionary into console text. |
| `sample_data.py` | The scenario catalogue: five generator scenarios with fixed seeds, plus two hand-built ones. |
| `tests.py` | 45 unit tests using the standard-library `unittest` module. |
| `data_generator.py`, `DATA_DESCRIPTION.md`, `example_usage.py` | Instructor-supplied starter files for Option B, not modified. |
| `requirements.txt` | States that only the standard library is used. |

The analysis is split across modules so each file has one job. `analysis.py` does not import `models.py`, so dependencies only go one way (models -> analysis).

## Installation and running

You need **Python 3.8 or later**. It was tested with Python 3.11 and 3.14. There are no packages to install.

```bash
git clone https://github.com/CLOBISO/ACIT4420.git
cd ACIT4420
python3 main.py
```

On Windows, or any system where the command is `python` rather than `python3`:

```bash
python main.py
```

Run the tests from the repository root:

```bash
python3 tests.py        # or: python tests.py
```

## Class design

| Class | Responsibility |
|---|---|
| `AcousticProfile` | The speaker's usual pitch, energy, speech rate and pause ratio. Every value is checked against its valid range when it is set. |
| `Speaker` | A speaker ID together with its `AcousticProfile`. |
| `AcousticWindow` | One observation window. It validates itself when created, keeps its list of issues (these make it unusable) and warnings (these only flag it), and returns feature values only when they are valid. |
| `RecordingSession` | One recording: a `Speaker` and its `AcousticWindow` objects. Gives access to all, usable, rejected and flagged windows. |
| `Assessment` | Base class for one way of interpreting a session. It defines `evaluate()` and a shared result format. |
| `StyleAssessment` | Subclass that decides the speaking-style label and gives reasons. |
| `QualityAssessment` | Subclass that scores recording quality and gives reasons. |
| `SessionAnalyzer` | Runs the calculations and every assessment on a session, and builds the result dictionary. |

### Where each OOP concept is demonstrated

- **Composition**
  - `Speaker` has an `AcousticProfile`.
  - `RecordingSession` has a `Speaker` and a list of `AcousticWindow` objects.
  - `SessionAnalyzer` has a list of `Assessment` objects.
- **Encapsulation**
  - `AcousticProfile` stores its values in protected attributes (`_pitch`, `_energy`, ...). They are reached through properties whose setters refuse invalid values, so a profile can never hold an impossible value.
  - `RecordingSession._windows` can only grow through `add_window()`, which accepts only `AcousticWindow` objects. The `windows` property returns a tuple, so callers cannot change the list.
  - `AcousticWindow` keeps its raw data, issues and warnings in protected attributes.
- **Inheritance and overriding**
  - `StyleAssessment` and `QualityAssessment` inherit from `Assessment`. Each overrides `evaluate()` and `name`.
  - `SessionAnalyzer` calls `evaluate()` on each assessment without knowing its type (polymorphism), so a new assessment can be added without changing the analyzer.
  - The base `evaluate()` raises `NotImplementedError`.
- **Class methods and static methods**
  - `AcousticProfile.from_dict()`, `Speaker.from_dict()` and `RecordingSession.from_data()` are **class methods**. They are alternative constructors that translate the generator's dictionary format (for example `usual_pitch`) into objects, so this translation lives in one place.
  - `QualityAssessment.score()` is a **static method**. The scoring formula belongs to the quality assessment but needs no instance state, and the tests call it directly.
  - `AcousticProfile._checked()` is a static method for the same reason.
- **Standalone functions**
  - In `analysis.py`: `validate_observation`, `check_feature`, `is_number`, `in_range`, `summarise_feature`, `summarise_session`, `compare_with_profile`, `coefficient_of_variation`, `count_windows` and `round_for_display`.
  - In `report.py`: `format_report`, `format_feature_table`, `format_window_notes`, `format_assessment`, `format_change`, `format_number` and `print_report`.

## Design decisions

 - Four domain classes: speaker, profile, window, session.
 - Inheritance only for the assessments. Both take the same inputs and return a label with reasons, so SessionAnalyzer can run them in a loop. Everything else is composition.
 - A bad profile raises an error, since every comparison depends on it.
 - A bad window is kept and marked unusable, so the rest of the session still counts and the report can show why it was rejected.
 - Windows validate themselves in the constructor, so the checks run once.
 - Rejected means impossible values or signal quality below 0.35. Flagged means valid values with quality below 0.60 or noise above 0.60. The 0.35 cut-off keeps the noisy scenario's windows (quality about 0.38 to 0.72) in the analysis, so that session is labelled noise affected.
 - Style rules run in order: insufficient data, noise, variation, energetic, deliberate, consistent. Noise goes before energetic because noise raises energy and pitch. Variation goes before energetic because a short burst can shift the mean.
 - Energetic needs higher energy plus a faster rate or higher pitch, since energy alone can be a closer microphone. Deliberate needs a slower rate plus more pauses, since a slower rate alone can be tiredness.
 - Quality score: 50% signal quality, 30% low noise, 20% usable windows. Noise is what the listener hears, missing windows are the least audible.
 - Thresholds come from DATA_DESCRIPTION.md.

## Assumptions and rules

### Assumptions

- The ranges in `DATA_DESCRIPTION.md` define which values are physically possible.
- The speaker's stored profile accurately represents their normal voice.
- Every window covers the same length of time, so each window counts equally.
- `signal_quality` is a trustworthy reliability score produced by the extraction tool.
- Each session contains one speaker only.
- `speech_rate` is approximately words per minute, as described in `DATA_DESCRIPTION.md`.
- The order of windows does not affect the classification; timestamps are used only to identify windows in the report.

### Validation

The valid ranges come from `DATA_DESCRIPTION.md`.

| Rule | Result |
|---|---|
| A required field is missing, the observation is not a dictionary, `timestamp` is not a whole number of 0 or more, or `speech_present` is not `True` or `False` | Rejected |
| `speech_present` is `False` | Rejected: "no usable speech detected" |
| With speech present, pitch is outside 45-450 Hz, energy outside 0-1, speech rate outside 30-260, or pause ratio outside 0-1. `None`, text, `True`/`False` and NaN also count as invalid. | Rejected |
| Background noise or signal quality is outside 0-1 | Rejected |
| Signal quality is below 0.35 | Rejected as unreliable |
| Signal quality is from 0.35 up to 0.60 | Kept, but flagged as low quality |
| Background noise is above 0.60 | Kept, but flagged as noisy |

A flagged window is still used in the analysis. The flags explain why the quality score is lower.

### Summaries

- Pitch, energy, speech rate and pause ratio are summarised over **usable** windows.
- Background noise and signal quality describe the whole recording, so they use **every window where the value is valid**, including windows without speech.

### Speaking style (first matching rule wins)

1. **Insufficient data:** fewer than 3 usable windows, or less than 50% of the windows are usable.
2. **Noise affected:** average background noise is 0.50 or more, or average signal quality is below 0.70. This is checked before the style rules because noise inflates measured energy and pitch.
3. **Temporarily varied:** the style changes *within* the session. This means pitch varies by more than 8% around its mean, speech rate by more than 12%, or the energy standard deviation is above 0.08. It is checked before energetic and deliberate: a short burst can move the average, but only an uneven session has a large spread.
4. **Energetic:** energy is at least 0.10 above usual, and either the speech rate is at least 10% faster or the pitch is at least 7% higher.
5. **Deliberate:** speech rate is at least 12% slower than usual, and the pause ratio is at least 0.08 higher.
6. **Consistent:** none of the rules above apply.

The energetic, deliberate and consistent rules compare values rounded to the precision shown in the report, so those decisions match the printed changes exactly. The noise and variation rules use unrounded values.

### Recording quality

`score = 100 x (0.5 x mean signal quality + 0.3 x (1 - mean background noise) + 0.2 x share of usable windows)`

| Score | Band |
|---|---|
| 75 or more | good |
| 55 to under 75 | acceptable |
| below 55 | poor |

If fewer than half the windows are usable, the band is capped at **acceptable**.

## Scenarios

| # | Scenario | Source | Style result | Quality result |
|---|---|---|---|---|
| 1 | Consistent speaking style | generator `consistent`, seed 11 | consistent | good (91.7) |
| 2 | Energetic delivery | generator `energetic`, seed 12 | energetic | good (92.0) |
| 3 | Slow, deliberate delivery | generator `deliberate`, seed 13 | deliberate | good (93.1) |
| 4 | High background noise | generator `noise_affected`, seed 14 | noise affected | poor (53.7) |
| 5 | Missing speech and poor recording quality | generator `insufficient_data`, seed 15 | insufficient data | poor (23.9) |
| 6 | Burst of livelier speech mid-session | hand-built from a consistent session | temporarily varied | good (92.6) |
| 7 | Malformed input data | hand-built: missing field, text, Boolean, negative timestamp, impossible pitch, `None`, non-dictionary row | insufficient data | acceptable (capped) |

`main.py` also shows that a speaker profile with an impossible usual pitch is rejected.

## Example output

The first report, from `python3 main.py`:

```text
==========================================================================
Consistent speaking style  |  speaker SP001
--------------------------------------------------------------------------
Windows: 12 total, 12 usable, 0 rejected, 0 flagged

Feature                Mean     Min     Max   Stdev   Usual   Change
--------------------------------------------------------------------
Pitch (Hz)            152.8   144.6   163.4     4.9   150.2    +1.8%
Energy                 0.40    0.36    0.43    0.02    0.39    +0.01
Speech rate (wpm)     145.3   138.0   151.0     3.9   144.0    +0.9%
Pause ratio            0.26    0.23    0.29    0.02    0.26    +0.00
Background noise       0.12    0.05    0.18    0.04
Signal quality         0.90    0.85    0.98    0.04

Speaking style: CONSISTENT
  - all speech features stay within the thresholds of the usual profile
  - pitch +1.8%, energy +0.01, speech rate +0.9%, pause ratio +0.00
Recording quality: GOOD (91.7/100)
  - average signal quality 0.90 (50% of the score)
  - average background noise 0.12 (30% of the score, lower is better)
  - 12 of 12 windows usable (20% of the score)
  - 91.7 is in the 'good' band (good >= 75, acceptable >= 55, otherwise poor)
```

The malformed-input report shows the validation messages:

```text
Rejected windows
  t=3    missing field(s): pitch
  t=4    pitch must be a number, got '151 Hz'
  t=5    energy must be a number, got True
  t=-1   timestamp must be a whole number of 0 or more, got -1
  t=7    pitch 910.0 is outside the valid range 45-450
  t=8    speech_rate is missing (None)
  t=9    speech_present must be True or False, got 'yes'
  t=None not an observation dictionary (str)

Speaking style: INSUFFICIENT DATA
  - only 3 of 11 windows are usable; at least 3 and at least 50% are needed
Recording quality: ACCEPTABLE (79.0/100)
  ...
  - capped at 'acceptable' because fewer than 50% of the windows are usable
```

## Testing

`tests.py` has 45 tests covering:

- validation boundaries and invalid types;
- profile and session encapsulation;
- the summary statistics;
- each style rule and the quality score;
- edge cases (an empty session, a fully rejected session and a single window); and
- the structure of the result dictionary.

It also runs all five generator scenarios with 30 seeds each and checks that each gets its expected label. A wider check of 500 seeds per scenario at 12 and 30 windows gave the expected label every time.

## Known limitations

- **Heuristic thresholds.** The thresholds are rules of thumb, tuned on the simulated data. Real recordings would need recalibration.
- **Small sessions.** With the generator's minimum of 6 windows, about 1 in 200 energetic or deliberate sessions is labelled "temporarily varied", because a small sample exaggerates the spread. At 12 or more windows this did not happen in testing.
- **One label only.** The first matching rule wins, so a session gets one label. For example, a noisy session that is also energetic is reported only as noise affected.
- **No time structure.** "Temporarily varied" is based on spread only; it does not locate *when* the change happened. Duplicate or out-of-order timestamps are not detected.
- **One stored profile per speaker.** The usual profile is taken as given and is not updated from new sessions.
- **Simulated data.** No real audio is used. Real voice features linked to a named speaker could be personal data (and possibly biometric data) under GDPR, so real use would need a data-protection review.
