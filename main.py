"""Podcast Voice and Recording Analyzer: runs every sample scenario and prints a report."""

from analysis import SessionAnalyzer
from models import RecordingSession, Speaker
from report import print_report
from sample_data import INVALID_PROFILE, load_scenarios


def demonstrate_profile_validation():
    print("Profile validation")
    try:
        Speaker.from_dict(INVALID_PROFILE)
    except (TypeError, ValueError) as error:
        print(f"  Speaker {INVALID_PROFILE['speaker_id']} rejected: {error}")
    else:
        print(f"  Speaker {INVALID_PROFILE['speaker_id']} was accepted, which should not happen")


def main():
    analyzer = SessionAnalyzer()
    for scenario in load_scenarios():
        session = RecordingSession.from_data(
            scenario["profile"], scenario["observations"], scenario["title"]
        )
        print_report(analyzer.analyze(session))
    demonstrate_profile_validation()


if __name__ == "__main__":
    main()
