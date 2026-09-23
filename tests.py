"""Unit tests for the Podcast Voice and Recording Analyzer.

Run from the repository root with:  python3 tests.py
"""

import unittest

from analysis import (
    Assessment,
    QualityAssessment,
    SessionAnalyzer,
    StyleAssessment,
    coefficient_of_variation,
    round_for_display,
    summarise_feature,
    validate_observation,
)
from data_generator import generate_recording_data
from models import AcousticProfile, AcousticWindow, RecordingSession, Speaker
from sample_data import INVALID_PROFILE, malformed_input_scenario, temporarily_varied_scenario

PROFILE = {
    "speaker_id": "T001",
    "usual_pitch": 150.0,
    "usual_energy": 0.40,
    "usual_speech_rate": 120,
    "usual_pause_ratio": 0.25,
}


def make_observation(timestamp=0, **changes):
    """A valid observation matching PROFILE, with optional changes."""
    observation = {
        "timestamp": timestamp,
        "speech_present": True,
        "pitch": 150.0,
        "energy": 0.40,
        "speech_rate": 120,
        "pause_ratio": 0.25,
        "background_noise": 0.10,
        "signal_quality": 0.92,
    }
    observation.update(changes)
    return observation


def analyze(observations, profile=PROFILE):
    return SessionAnalyzer().analyze(RecordingSession.from_data(profile, observations, "test"))


class ValidationTests(unittest.TestCase):
    def test_valid_observation_has_no_issues_or_warnings(self):
        self.assertEqual(validate_observation(make_observation()), ([], []))

    def test_range_boundaries_are_inclusive(self):
        for feature, low, high in (
            ("pitch", 45, 450),
            ("energy", 0, 1),
            ("speech_rate", 30, 260),
            ("pause_ratio", 0, 1),
            ("background_noise", 0, 0.6),
        ):
            for value in (low, high):
                with self.subTest(feature=feature, value=value):
                    issues, _ = validate_observation(make_observation(**{feature: value}))
                    self.assertEqual(issues, [])

    def test_values_just_outside_range_are_rejected(self):
        for feature, value in (
            ("pitch", 44.9),
            ("pitch", 450.1),
            ("energy", -0.01),
            ("speech_rate", 261),
            ("pause_ratio", 1.25),
            ("background_noise", 1.01),
            ("signal_quality", 1.5),
        ):
            with self.subTest(feature=feature, value=value):
                issues, _ = validate_observation(make_observation(**{feature: value}))
                self.assertTrue(any(feature in issue for issue in issues), issues)

    def test_none_and_wrong_types_are_rejected(self):
        for value in (None, "148", True, float("nan")):
            with self.subTest(value=value):
                issues, _ = validate_observation(make_observation(pitch=value))
                self.assertTrue(issues)

    def test_missing_field_is_reported(self):
        observation = make_observation()
        del observation["energy"]
        issues, _ = validate_observation(observation)
        self.assertIn("missing field(s): energy", issues)

    def test_bad_timestamp_and_speech_flag_are_rejected(self):
        for changes in ({"timestamp": -1}, {"timestamp": 1.5}, {"speech_present": "yes"}):
            with self.subTest(changes=changes):
                issues, _ = validate_observation(make_observation(**changes))
                self.assertTrue(issues)

    def test_window_without_speech_is_excluded(self):
        observation = make_observation(
            speech_present=False, pitch=None, energy=None, speech_rate=None, pause_ratio=None
        )
        issues, _ = validate_observation(observation)
        self.assertEqual(issues, ["no usable speech detected"])

    def test_signal_quality_thresholds(self):
        issues, warnings = validate_observation(make_observation(signal_quality=0.30))
        self.assertTrue(any("unreliable" in issue for issue in issues))
        issues, warnings = validate_observation(make_observation(signal_quality=0.50))
        self.assertEqual(issues, [])
        self.assertEqual(warnings, ["low signal quality 0.50"])

    def test_high_noise_is_flagged_not_rejected(self):
        issues, warnings = validate_observation(make_observation(background_noise=0.75))
        self.assertEqual(issues, [])
        self.assertEqual(warnings, ["high background noise 0.75"])

    def test_non_dictionary_is_rejected(self):
        issues, _ = validate_observation("corrupted row")
        self.assertEqual(len(issues), 1)


class ProfileAndSpeakerTests(unittest.TestCase):
    def test_from_dict_builds_profile(self):
        profile = AcousticProfile.from_dict(PROFILE)
        self.assertEqual(profile.speech_rate, 120)
        self.assertEqual(profile.as_dict()["pitch"], 150.0)

    def test_missing_profile_field_raises(self):
        incomplete = dict(PROFILE)
        del incomplete["usual_energy"]
        with self.assertRaises(ValueError):
            AcousticProfile.from_dict(incomplete)

    def test_invalid_profile_value_raises(self):
        with self.assertRaises(ValueError):
            Speaker.from_dict(INVALID_PROFILE)

    def test_setter_protects_profile(self):
        profile = AcousticProfile.from_dict(PROFILE)
        with self.assertRaises(ValueError):
            profile.energy = 1.5
        self.assertEqual(profile.energy, 0.40)

    def test_speaker_needs_id_and_profile(self):
        profile = AcousticProfile.from_dict(PROFILE)
        with self.assertRaises(ValueError):
            Speaker("  ", profile)
        with self.assertRaises(TypeError):
            Speaker("T001", PROFILE)


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.session = RecordingSession(Speaker.from_dict(PROFILE))

    def test_windows_are_read_only_tuple(self):
        self.session.add_window(AcousticWindow(make_observation()))
        self.assertIsInstance(self.session.windows, tuple)
        self.assertEqual(len(self.session.windows), 1)

    def test_only_windows_can_be_added(self):
        with self.assertRaises(TypeError):
            self.session.add_window(make_observation())

    def test_usable_rejected_and_flagged_windows(self):
        self.session.add_observations([
            make_observation(0),
            make_observation(1, pitch=None),
            make_observation(2, signal_quality=0.5),
        ])
        self.assertEqual(len(self.session.usable_windows), 2)
        self.assertEqual(len(self.session.rejected_windows), 1)
        self.assertEqual(len(self.session.flagged_windows), 1)

    def test_session_needs_speaker(self):
        with self.assertRaises(TypeError):
            RecordingSession("T001")


class CalculationTests(unittest.TestCase):
    def test_summary_of_known_values(self):
        stats = summarise_feature([2, 4, 4, 4, 5, 5, 7, 9])
        self.assertEqual(stats["count"], 8)
        self.assertEqual(stats["mean"], 5)
        self.assertEqual(stats["min"], 2)
        self.assertEqual(stats["max"], 9)
        self.assertAlmostEqual(stats["stdev"], 2.138, places=3)

    def test_summary_of_empty_and_single_value(self):
        self.assertIsNone(summarise_feature([]))
        self.assertEqual(summarise_feature([3.5])["stdev"], 0.0)

    def test_coefficient_of_variation(self):
        self.assertAlmostEqual(coefficient_of_variation({"mean": 100, "stdev": 8}), 0.08)
        self.assertEqual(coefficient_of_variation(None), 0.0)

    def test_round_for_display_removes_negative_zero(self):
        self.assertEqual(f"{round_for_display(-0.001, 2):+.2f}", "+0.00")

    def test_noise_and_quality_use_windows_without_speech(self):
        observations = [make_observation(i) for i in range(3)]
        observations.append(make_observation(
            3, speech_present=False, pitch=None, energy=None, speech_rate=None,
            pause_ratio=None, background_noise=0.50,
        ))
        result = analyze(observations)
        self.assertEqual(result["summary"]["pitch"]["count"], 3)
        self.assertEqual(result["summary"]["background_noise"]["count"], 4)


class StyleRuleTests(unittest.TestCase):
    def label(self, observations):
        return analyze(observations)["style"]["label"]

    def test_consistent(self):
        self.assertEqual(self.label([make_observation(i) for i in range(6)]), "consistent")

    def test_energetic(self):
        observations = [make_observation(i, energy=0.55, speech_rate=135) for i in range(6)]
        self.assertEqual(self.label(observations), "energetic")

    def test_energy_alone_is_not_energetic(self):
        observations = [make_observation(i, energy=0.55) for i in range(6)]
        self.assertEqual(self.label(observations), "consistent")

    def test_deliberate(self):
        observations = [make_observation(i, speech_rate=100, pause_ratio=0.35) for i in range(6)]
        self.assertEqual(self.label(observations), "deliberate")

    def test_noise_affected(self):
        observations = [make_observation(i, background_noise=0.8) for i in range(6)]
        self.assertEqual(self.label(observations), "noise affected")

    def test_temporarily_varied(self):
        observations = [make_observation(i) for i in range(6)]
        observations += [make_observation(i, energy=0.70, pitch=190.0) for i in range(6, 9)]
        self.assertEqual(self.label(observations), "temporarily varied")

    def test_insufficient_data_when_too_few_windows(self):
        self.assertEqual(self.label([make_observation(0), make_observation(1)]), "insufficient data")

    def test_insufficient_data_when_under_half_usable(self):
        observations = [make_observation(i) for i in range(3)]
        observations += [make_observation(i, pitch=None) for i in range(3, 7)]
        self.assertEqual(self.label(observations), "insufficient data")

    def test_empty_and_fully_rejected_sessions_do_not_crash(self):
        self.assertEqual(self.label([]), "insufficient data")
        rejected = [make_observation(i, signal_quality=0.1) for i in range(5)]
        result = analyze(rejected)
        self.assertEqual(result["style"]["label"], "insufficient data")
        self.assertIsNone(result["summary"]["pitch"])

    def test_single_usable_window(self):
        self.assertEqual(self.label([make_observation(0)]), "insufficient data")


class QualityTests(unittest.TestCase):
    def test_score_formula(self):
        self.assertEqual(QualityAssessment.score(1.0, 0.0, 1.0), 100.0)
        self.assertEqual(QualityAssessment.score(0.0, 1.0, 0.0), 0.0)
        self.assertEqual(QualityAssessment.score(0.8, 0.2, 0.5), 74.0)

    def test_clean_recording_is_good(self):
        result = analyze([make_observation(i) for i in range(6)])
        self.assertEqual(result["quality"]["label"], "good")

    def test_good_is_capped_when_most_windows_unusable(self):
        observations = [make_observation(i) for i in range(3)]
        observations += [make_observation(i, pitch=None) for i in range(3, 10)]
        self.assertEqual(analyze(observations)["quality"]["label"], "acceptable")

    def test_empty_session_cannot_be_evaluated(self):
        self.assertEqual(analyze([])["quality"]["label"], "cannot be evaluated")


class AnalyzerTests(unittest.TestCase):
    def test_result_has_required_keys_and_counts_add_up(self):
        result = analyze([make_observation(0), make_observation(1, pitch=None)])
        for key in ("speaker_id", "session_title", "windows", "rejections", "warnings",
                    "summary", "comparison", "style", "quality"):
            self.assertIn(key, result)
        counts = result["windows"]
        self.assertEqual(counts["usable"] + counts["rejected"], counts["total"])
        self.assertEqual(len(result["rejections"]), counts["rejected"])

    def test_base_assessment_must_be_overridden(self):
        with self.assertRaises(NotImplementedError):
            Assessment().evaluate({}, {}, {})

    def test_analyzer_rejects_non_assessments(self):
        with self.assertRaises(TypeError):
            SessionAnalyzer(["style"])

    def test_assessments_are_polymorphic(self):
        analyzer = SessionAnalyzer([StyleAssessment()])
        session = RecordingSession.from_data(PROFILE, [make_observation(i) for i in range(4)])
        result = analyzer.analyze(session)
        self.assertIn("style", result)
        self.assertNotIn("quality", result)


class ScenarioTests(unittest.TestCase):
    EXPECTED = {
        "consistent": "consistent",
        "energetic": "energetic",
        "deliberate": "deliberate",
        "noise_affected": "noise affected",
        "insufficient_data": "insufficient data",
    }

    def test_generator_scenarios_over_many_seeds(self):
        for scenario, expected in self.EXPECTED.items():
            for seed in range(30):
                with self.subTest(scenario=scenario, seed=seed):
                    profile, observations = generate_recording_data("SPX", scenario, seed, 12)
                    self.assertEqual(analyze(observations, profile)["style"]["label"], expected)

    def test_hand_built_varied_scenario(self):
        scenario = temporarily_varied_scenario()
        result = analyze(scenario["observations"], scenario["profile"])
        self.assertEqual(result["style"]["label"], "temporarily varied")

    def test_malformed_scenario(self):
        scenario = malformed_input_scenario()
        result = analyze(scenario["observations"], scenario["profile"])
        self.assertEqual(result["windows"]["usable"], 3)
        self.assertEqual(result["windows"]["rejected"], 8)
        self.assertEqual(result["style"]["label"], "insufficient data")


if __name__ == "__main__":
    unittest.main()
