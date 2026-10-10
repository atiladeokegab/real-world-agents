"""§4.3 tool catalogue. The ten services are the read tools (risk 1) plus case_journal and
portal_delivery (risk 2). A change on a service is its own entry, `<service>.<action>`, because
a ToolSpec carries one risk level and the verifier and eval read risk per tool name."""

from agent.tools._contracts import ToolSpec

PERSONAL = "Bank customer"
BUSINESS = "Authorised business user"
ANYONE = [PERSONAL, BUSINESS]

SERVICES = [
    "transfer_journal", "standing_order_journal", "mandate_journal", "card_service",
    "profile_service", "statements_service", "fees_service", "business_service",
    "case_journal", "portal_delivery",
]


def _read(name: str, **inputs: str) -> ToolSpec:
    return ToolSpec(name=name, inputs={"query": "str", **inputs}, roles=ANYONE, risk=1)


def _write(name: str, risk: int, key_fields: list[str], read_back: str | None, strength: str = "strong",
           roles: list[str] = ANYONE, required_reads: list[str] | None = None, **inputs: str) -> ToolSpec:
    """key_fields[0] is the target (account, order, batch, card, reference) the intent is about."""
    reads = [read_back] if required_reads is None and read_back else (required_reads or [])
    return ToolSpec(name=name, inputs={f: "str" for f in key_fields} | inputs, roles=roles, risk=risk,
                    required_reads=reads, read_back=read_back, read_strength=strength, key_fields=key_fields)


_SPECS = [
    # reads, risk 1: autonomous (§4.6)
    _read("transfer_journal", reference="str", amount="str", date="str"),
    _read("standing_order_journal", reference="str"),
    _read("mandate_journal", reference="str"),
    _read("card_service", card="str"),
    _read("profile_service", field="str"),
    _read("statements_service", period="str"),
    _read("fees_service", fee="str", date="str"),
    _read("business_service", batch="str", person="str"),
    # inform, risk 2: autonomous after the claim linter
    _write("case_journal", 2, ["subject", "kind"], None, detail="str"),
    _write("portal_delivery", 2, ["artifact", "recipient"], None, detail="str"),
    _write("statements_service.request", 2, ["period", "kind"], "statements_service", "lagging"),
    _write("fees_service.review", 2, ["fee", "amount"], "fees_service", "lagging", reason="str"),
    # changes / money, risk 3: verified identity, in mandate, required reads in the trace
    _write("transfer_journal.return_request", 3, ["reference", "amount", "payee"], "transfer_journal", "lagging",
           roles=ANYONE),
    _write("standing_order_journal.cancel", 3, ["reference"], "standing_order_journal", roles=[PERSONAL]),
    _write("standing_order_journal.amend", 3, ["reference", "amount", "date"], "standing_order_journal",
           roles=[PERSONAL]),
    _write("mandate_journal.cancel", 3, ["reference"], "mandate_journal", roles=ANYONE),
    _write("mandate_journal.dispute", 3, ["reference", "amount", "date"], "mandate_journal", "lagging",
           roles=ANYONE),
    _write("card_service.block", 3, ["card"], "card_service", roles=[PERSONAL]),
    _write("card_service.dispute", 3, ["card", "amount", "reference"], "card_service", "lagging",
           roles=[PERSONAL]),
    _write("profile_service.change", 3, ["field", "value"], "profile_service", roles=[PERSONAL]),
    _write("business_service.role_change", 3, ["person", "role"], "business_service", roles=[BUSINESS]),
    _write("business_service.release_batch", 3, ["batch", "amount"], "business_service", roles=[BUSINESS]),
    _write("business_service.reissue_rows", 3, ["batch", "rows", "amount"], "business_service",
           roles=[BUSINESS]),
]

CATALOGUE: dict[str, ToolSpec] = {s.name: s for s in _SPECS}


def service_of(tool: str) -> str:
    return tool.split(".", 1)[0]


def is_write(spec: ToolSpec) -> bool:
    return spec.risk > 1
