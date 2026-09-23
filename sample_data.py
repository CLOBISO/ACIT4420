"""Scenario catalogue used by main.py and tests.py.

Five scenarios come straight from the instructor-supplied generator with fixed
seeds, so every run gives the same data. Two are built here: the generator has
no "temporarily varied" scenario, and malformed input needs values the
generator never produces. The scenario dictionaries do not include an expected
label; the analysis has to work that out.
"""

from data_generator import generate_recording_data

NUMBER_OF_WINDOWS = 12

# (title, speaker id, generator scenario, seed)
GENERATOR_SCENARIOS = (
    ("Consistent speaking style", "SP001", "consistent", 11),
    ("Energetic delivery", "SP002", "energetic", 12),
    ("Slow, deliberate delivery", "SP003", "deliberate", 13),
    ("High background noise", "SP004", "noise_affected", 14),
    ("Missing speech and poor recording quality", "SP005", "insufficient_data", 15),
)

# A profile with an impossible usual pitch, used to show profile validation.
INVALID_PROFILE = {
    "speaker_id": "SP008",
    "usual_pitch": -120.0,
    "usual_energy": 0.35,
    "usual_speech_rate": 120,
    "usual_pause_ratio": 0.25,
}


def generator_scenario(title, speaker_id, scenario, seed, number_of_windows=NUMBER_OF_WINDOWS):
    profile, observations = generate_recording_data(
        speaker_id=speaker_id,
        scenario=scenario,
        seed=seed,
        number_of_windows=number_of_windows,
    )
    return {"title": title, "profile": profile, "observations": observations}


def temporarily_varied_scenario(seed=21):
    """A consistent session with a livelier burst in the middle four windows."""
    profile, observations = generate_recording_data(
        speaker_id="SP006",
        scenario="consistent",
        seed=seed,
        number_of_windows=NUMBER_OF_WINDOWS,
    )
    for observation in observations[4:8]:
        observation["energy"] = round(min(1.0, observation["energy"] + 0.25), 2)
        observation["speech_rate"] = observation["speech_rate"] + 35
        observation["pitch"] = round(observation["pitch"] * 1.2, 1)
        observation["pause_ratio"] = round(max(0.0, observation["pause_ratio"] - 0.08), 2)
    return {
        "title": "Burst of livelier speech mid-session",
        "profile": profile,
        "observations": observations,
    }


def malformed_input_scenario():
    """Three valid windows mixed with the kinds of bad data a real pipeline can produce."""
    profile = {
        "speaker_id": "SP007",
        "usual_pitch": 150.0,
        "usual_energy": 0.40,
        "usual_speech_rate": 125,
        "usual_pause_ratio": 0.22,
    }

    def window(timestamp, **changes):
        observation = {
            "timestamp": timestamp,
            "speech_present": True,
            "pitch": 151.0,
            "energy": 0.41,
            "speech_rate": 124,
            "pause_ratio": 0.22,
            "background_noise": 0.10,
            "signal_quality": 0.93,
        }
        observation.update(changes)
        return observation

    missing_pitch = window(3)
    del missing_pitch["pitch"]

    observations = [
        window(0),
        window(1, pitch=149.5, energy=0.39),
        window(2, speech_rate=127),
        missing_pitch,                       # a field is missing
        window(4, pitch="151 Hz"),           # text instead of a number
        window(5, energy=True),              # Boolean instead of a number
        window(-1),                          # impossible timestamp
        window(7, pitch=910.0),              # impossible pitch
        window(8, speech_rate=None),         # speech present but no rate
        window(9, speech_present="yes"),     # not a Boolean
        "corrupted row",                     # not a dictionary at all
    ]
    return {"title": "Malformed input data", "profile": profile, "observations": observations}


def load_scenarios():
    """Return all seven scenarios in the order main.py reports them."""
    scenarios = [generator_scenario(*entry) for entry in GENERATOR_SCENARIOS]
    scenarios.append(temporarily_varied_scenario())
    scenarios.append(malformed_input_scenario())
    return scenarios
