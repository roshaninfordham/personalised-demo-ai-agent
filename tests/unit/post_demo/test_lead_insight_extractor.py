from services.api.tests.test_post_demo_intelligence import _bundle

from live_demo_api.post_demo.insights.lead_insight_extractor import LeadInsightExtractor


def test_unit_lead_insight_extractor_uses_valid_evidence() -> None:
    insights = LeadInsightExtractor().extract(_bundle())

    assert insights
    assert all(insight.evidence_transcript_event_ids for insight in insights)
