from agent.llm.prompts import catalogue_summary
from agent.tools.catalogue import HOLDS, SERVICES


def test_every_service_says_what_it_holds():
    assert set(HOLDS) == set(SERVICES)
    assert all(HOLDS[s] for s in SERVICES)


def test_statements_service_holds_documents_and_confirmation_letters():
    assert "documents" in HOLDS["statements_service"] and "confirmation letters" in HOLDS["statements_service"]


def test_catalogue_summary_shows_each_description():
    summary = catalogue_summary()
    for service, holds in HOLDS.items():
        assert f"- {service}: holds {holds}; inputs" in summary
