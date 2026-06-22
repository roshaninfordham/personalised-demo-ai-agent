from services.api.tests.test_post_demo_intelligence import _bundle

from live_demo_api.post_demo.features.feature_shown_tracker import FeatureShownTracker


def test_unit_feature_shown_tracker_merges_reporting_evidence() -> None:
    features = FeatureShownTracker().track(_bundle())

    assert any(feature.feature_category == "reporting" for feature in features)
    assert all(feature.confidence >= 0.45 for feature in features)
