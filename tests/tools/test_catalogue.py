from agent.tools import CATALOGUE, SERVICES
from agent.tools.catalogue import service_of


def test_ten_services_present():
    assert len(SERVICES) == 10 and set(SERVICES) <= set(CATALOGUE)


def test_every_tool_belongs_to_a_service():
    assert {service_of(n) for n in CATALOGUE} == set(SERVICES)


def test_names_match_keys_and_risk_in_range():
    for name, spec in CATALOGUE.items():
        assert spec.name == name and spec.risk in (1, 2, 3)


def test_reads_are_risk_one_without_keys():
    for name in SERVICES[:8]:
        assert CATALOGUE[name].risk == 1 and not CATALOGUE[name].key_fields


def test_references_resolve():
    for spec in CATALOGUE.values():
        assert all(r in CATALOGUE for r in spec.required_reads)
        assert spec.read_back is None or CATALOGUE[spec.read_back].risk == 1


def test_writes_have_keys_and_risk_three_has_reads_and_roles():
    for spec in CATALOGUE.values():
        if spec.risk > 1:
            assert spec.key_fields and all(f in spec.inputs for f in spec.key_fields)
        if spec.risk == 3:
            assert spec.required_reads and spec.roles and spec.read_back
