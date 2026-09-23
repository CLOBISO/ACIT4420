"""Domain classes for the Podcast Voice and Recording Analyzer.

A Speaker has an AcousticProfile (their usual voice). A RecordingSession has a
Speaker and the AcousticWindow objects recorded in that session.
"""

from analysis import FEATURE_LIMITS, in_range, validate_observation


class AcousticProfile:
    """A speaker's usual pitch, energy, speech rate and pause ratio."""

    # Attribute name -> key used in the generator's profile dictionary.
    PROFILE_KEYS = {
        "pitch": "usual_pitch",
        "energy": "usual_energy",
        "speech_rate": "usual_speech_rate",
        "pause_ratio": "usual_pause_ratio",
    }

    def __init__(self, pitch, energy, speech_rate, pause_ratio):
        # Assigning through the properties validates every value.
        self.pitch = pitch
        self.energy = energy
        self.speech_rate = speech_rate
        self.pause_ratio = pause_ratio

    @classmethod
    def from_dict(cls, profile):
        """Build a profile from the generator's dictionary (usual_pitch, usual_energy, ...)."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")
        missing = [key for key in cls.PROFILE_KEYS.values() if key not in profile]
        if missing:
            raise ValueError("profile is missing: " + ", ".join(missing))
        return cls(**{attr: profile[key] for attr, key in cls.PROFILE_KEYS.items()})

    @staticmethod
    def _checked(feature, value):
        low, high = FEATURE_LIMITS[feature]
        if not in_range(value, low, high):
            raise ValueError(f"usual {feature} must be a number between {low} and {high}, got {value!r}")
        return value

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, value):
        self._pitch = self._checked("pitch", value)

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = self._checked("energy", value)

    @property
    def speech_rate(self):
        return self._speech_rate

    @speech_rate.setter
    def speech_rate(self, value):
        self._speech_rate = self._checked("speech_rate", value)

    @property
    def pause_ratio(self):
        return self._pause_ratio

    @pause_ratio.setter
    def pause_ratio(self, value):
        self._pause_ratio = self._checked("pause_ratio", value)

    def as_dict(self):
        return {attr: getattr(self, attr) for attr in self.PROFILE_KEYS}


class Speaker:
    """A podcast speaker and their usual acoustic profile (composition)."""

    def __init__(self, speaker_id, profile):
        if not isinstance(speaker_id, str) or not speaker_id.strip():
            raise ValueError("speaker_id must be a non-empty string")
        if not isinstance(profile, AcousticProfile):
            raise TypeError("profile must be an AcousticProfile")
        self._speaker_id = speaker_id.strip()
        self._profile = profile

    @classmethod
    def from_dict(cls, profile):
        """Build a Speaker and its AcousticProfile from one generator profile dictionary."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")
        return cls(profile.get("speaker_id"), AcousticProfile.from_dict(profile))

    @property
    def speaker_id(self):
        return self._speaker_id

    @property
    def profile(self):
        return self._profile


class AcousticWindow:
    """One short window of extracted speech features.

    The window validates itself when created. Issues make it unusable;
    warnings only flag it.
    """

    def __init__(self, observation):
        self._data = dict(observation) if isinstance(observation, dict) else {}
        self._issues, self._warnings = validate_observation(observation)

    @property
    def timestamp(self):
        return self._data.get("timestamp")

    @property
    def speech_present(self):
        return self._data.get("speech_present") is True

    @property
    def issues(self):
        return tuple(self._issues)

    @property
    def warnings(self):
        return tuple(self._warnings)

    @property
    def is_usable(self):
        return not self._issues

    @property
    def is_flagged(self):
        return self.is_usable and bool(self._warnings)

    def value(self, feature):
        """Return the feature value if it is present and within range, otherwise None."""
        low, high = FEATURE_LIMITS[feature]
        value = self._data.get(feature)
        return value if in_range(value, low, high) else None


class RecordingSession:
    """One recording by one speaker, made up of acoustic windows (composition)."""

    def __init__(self, speaker, title="Untitled session"):
        if not isinstance(speaker, Speaker):
            raise TypeError("speaker must be a Speaker")
        self._speaker = speaker
        self._title = str(title)
        self._windows = []

    @classmethod
    def from_data(cls, profile, observations, title="Untitled session"):
        """Build a complete session from the generator's (profile, observations) output."""
        session = cls(Speaker.from_dict(profile), title)
        session.add_observations(observations)
        return session

    @property
    def speaker(self):
        return self._speaker

    @property
    def title(self):
        return self._title

    @property
    def windows(self):
        """All windows as a tuple, so callers cannot change the list directly."""
        return tuple(self._windows)

    @property
    def usable_windows(self):
        return [window for window in self._windows if window.is_usable]

    @property
    def rejected_windows(self):
        return [window for window in self._windows if not window.is_usable]

    @property
    def flagged_windows(self):
        return [window for window in self._windows if window.is_flagged]

    def add_window(self, window):
        if not isinstance(window, AcousticWindow):
            raise TypeError("only AcousticWindow objects can be added to a session")
        self._windows.append(window)

    def add_observations(self, observations):
        """Wrap each raw observation in an AcousticWindow and add it."""
        for observation in observations:
            self.add_window(AcousticWindow(observation))
