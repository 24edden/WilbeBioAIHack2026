"""Offline hypothesis-state and continuation checks; no scientific truth claims."""
import copy

import pytest

from app.hypothesis_governance import INTERPRETATION_SCOPE, validate_governance
from app.provider_schemas import Investigation
from app.store import digest

HYPOTHESIS = "Antigen change explains resistance. Effector dysfunction is another explanation."
SOURCE = {"path": "sources/assay.tsv", "sha256": "a" * 64}
CASE = {"id": "test-case", "source_manifest": [SOURCE]}
RECIPE = {"id": "targeted-analysis", "kind": "data_analysis", "input_sources": [SOURCE]}
EVIDENCE = [
    {"id": "observed", "kind": "measured", "source": {"sha256": "b" * 64}, "values": {"contrast": 3}},
    {"id": "contradiction", "kind": "measured", "source": {"sha256": "c" * 64}, "values": {"contrast": -2}},
]
FOLLOWUP = {"analysis_id": RECIPE["id"], "kind": RECIPE["kind"], "status": "ready"}


def entry(**changes):
    result = {
        "hypothesis_id": "primary", "statement": "Antigen change explains resistance.",
        "origin": "user", "source_quote": "", "scope": "The supplied assay, without patient-level attribution.",
        "scope_type": "biological", "status": "possible",
        "rationale": "The available contrast leaves the proposed mechanism possible within this assay.",
        "supporting_evidence_ids": ["observed"], "contradicting_evidence_ids": [], "test_evidence_ids": [],
        "falsification_test": "", "falsification_result": "", "next_analysis_ids": [RECIPE["id"]], "blocker": "",
    }
    result.update(changes)
    return result


def ledger(**changes):
    result = {
        "hypotheses": [entry()], "next_action_id": RECIPE["id"], "target_hypothesis_ids": ["primary"],
        "continuation_reason": "The registered contrast can discriminate the remaining source-level explanations.",
        "stop_reason": "continue",
    }
    result.update(changes)
    return result


def check(value=None, **changes):
    arguments = dict(hypothesis=HYPOTHESIS, evidence=EVIDENCE, recipes=[RECIPE],
                     followups=[FOLLOWUP], previous=None, case=CASE)
    arguments.update(changes)
    return validate_governance(value if value is not None else ledger(), **arguments)


def stopped(item=None, reason="needs_data"):
    assessment = copy.deepcopy(item) if item is not None else entry()
    assessment["next_analysis_ids"] = []
    if assessment["status"] == "possible" and not assessment["blocker"]:
        assessment["blocker"] = "A paired functional measurement remains unavailable."
    return ledger(hypotheses=[assessment],
                  next_action_id=None, target_hypothesis_ids=[], stop_reason=reason,
                  continuation_reason="The available registered methods do not supply the missing functional measurement.")


def excluded(**changes):
    result = entry(status="clearly_ruled_out", supporting_evidence_ids=[],
                 contradicting_evidence_ids=["contradiction"], test_evidence_ids=["contradiction"],
                 falsification_test="The prespecified control comparison directly tested the scoped prediction.",
                 falsification_result="The observed direction contradicted the scoped prediction in this assay.",
                 next_analysis_ids=[])
    result.update(changes)
    return result


def test_valid_continuation_is_bound_to_exact_inputs_and_revalidates_after_normalization():
    result = check()
    assert result["next_action_id"] == RECIPE["id"]
    assert result["hypothesis_sha256"] == digest(HYPOTHESIS)
    assert result["evidence_versions"] == {"observed": EVIDENCE[0]["source"]["sha256"]}
    assert result["accepted_evidence_versions"] == {e["id"]: e["source"]["sha256"] for e in EVIDENCE}
    assert result["recipe_versions"] == {RECIPE["id"]: digest(RECIPE)}
    assert result["interpretation_scope"] == INTERPRETATION_SCOPE
    assert check(result) == result


def test_legacy_investigation_without_governance_remains_readable():
    from test_providers import decision
    original = decision()
    original.pop("governance", None)
    assert Investigation.model_validate(original).governance is None


@pytest.mark.parametrize("field", ["supporting_evidence_ids", "contradicting_evidence_ids", "test_evidence_ids"])
def test_fabricated_citations_are_rejected(field):
    value = ledger(hypotheses=[entry(**{field: ["fabricated"]})])
    with pytest.raises(ValueError, match="accepted evidence"):
        check(value)


@pytest.mark.parametrize("entries", [
    [entry(hypothesis_id="different")],
    [entry(), entry()],
    [entry(origin="agent_generated")],
    [entry(hypothesis_id="unsafe/id")],
])
def test_missing_primary_duplicate_and_invalid_identity_are_rejected(entries):
    with pytest.raises(ValueError):
        check(ledger(hypotheses=entries))


def test_user_alternative_requires_exact_original_quote_and_agent_alternative_is_separate():
    user = entry(hypothesis_id="effector", statement="Effector dysfunction is another explanation.",
                 source_quote="Effector dysfunction is another explanation.")
    result = check(ledger(hypotheses=[entry(), user]))
    assert result["hypotheses"][1]["origin"] == "user"
    for quote in ("", "Invented user hypothesis."):
        with pytest.raises(ValueError, match="source quotation"):
            check(ledger(hypotheses=[entry(), {**user, "source_quote": quote}]))
    with pytest.raises(ValueError, match="Agent-generated"):
        check(ledger(hypotheses=[entry(), {**user, "origin": "agent_generated"}]))


@pytest.mark.parametrize("changes", [
    {"supporting_evidence_ids": []},
    {"rationale": "Yes."},
])
def test_probable_requires_evidence_and_substantive_scoped_reason(changes):
    with pytest.raises(ValueError):
        check(stopped(entry(status="probable", **changes)))


@pytest.mark.parametrize("kind, values", [
    ("prediction", {}), ("analysis", {"structural_recipe_id": "some-structure"}),
    ("gap", {}), ("analysis", {"status": "blocked"}),
])
def test_prediction_or_missing_data_cannot_establish_biological_probability(kind, values):
    evidence = [{**EVIDENCE[0], "kind": kind, "values": values}, EVIDENCE[1]]
    with pytest.raises(ValueError, match="Probable requires"):
        check(stopped(entry(status="probable")), evidence=evidence)


@pytest.mark.parametrize("field", ["contradicting_evidence_ids", "test_evidence_ids", "falsification_test", "falsification_result", "scope"])
def test_rule_out_requires_an_explicit_scoped_completed_test(field):
    value = excluded()
    value[field] = [] if field.endswith("_ids") else ""
    with pytest.raises(ValueError):
        check(stopped(value, "resolved_within_scope"))


def test_completed_scoped_rule_out_passes_but_prediction_only_biological_exclusion_does_not():
    value = stopped(excluded(), "resolved_within_scope")
    assert check(value)["hypotheses"][0]["status"] == "clearly_ruled_out"
    prediction = [{**EVIDENCE[0]}, {**EVIDENCE[1], "kind": "prediction"}]
    with pytest.raises(ValueError, match="biological exclusion"):
        check(value, evidence=prediction)
    value["hypotheses"][0]["scope_type"] = "computational"
    value["hypotheses"][0]["scope"] = "This predictor's submitted monomer output and coordinate validity only."
    assert check(value, evidence=prediction)["hypotheses"][0]["status"] == "clearly_ruled_out"


def test_scoped_probable_and_excluded_hypotheses_can_stop_without_numeric_probabilities():
    result = check(stopped(entry(status="probable"), "resolved_within_scope"))
    assert result["hypotheses"][0]["status"] == "probable"
    with pytest.raises(ValueError, match="Unresolved possible"):
        check(stopped(reason="resolved_within_scope"))
    value = stopped(entry(status="probable"))
    value["hypotheses"][0]["probability"] = 0.9
    with pytest.raises(ValueError):
        check(value)


@pytest.mark.parametrize("reason", ["needs_data", "needs_method", "wet_lab_required", "no_informative_action", "provider_unresolved"])
def test_honest_stops_preserve_possible_status_and_reason(reason):
    result = check(stopped(reason=reason))
    assert result["hypotheses"][0]["status"] == "possible"
    assert result["next_action_id"] is None and result["continuation_reason"]


@pytest.mark.parametrize("changes", [
    {"next_action_id": "unknown"}, {"target_hypothesis_ids": []},
    {"target_hypothesis_ids": ["unknown"]}, {"continuation_reason": " "},
    {"hypotheses": [entry(next_analysis_ids=[])]},
    {"hypotheses": [excluded(next_analysis_ids=[RECIPE["id"]])]},
])
def test_continuation_requires_registered_action_valid_target_and_reason(changes):
    with pytest.raises(ValueError):
        check(ledger(**changes))


@pytest.mark.parametrize("followups", [
    [], [{**FOLLOWUP, "status": "needs_inputs"}],
    [{**FOLLOWUP, "executable": False}],
    [{**FOLLOWUP, "requested_status": "needs_inputs"}],
    [{**FOLLOWUP, "kind": "bionemo_public_structure"}],
    [FOLLOWUP, FOLLOWUP],
])
def test_continuation_requires_one_ready_qualified_final_followup(followups):
    with pytest.raises(ValueError, match="ready final"):
        check(followups=followups)


def test_completed_same_source_analysis_cannot_be_resubmitted_as_continuation():
    completed = {"id": "performed", "kind": "analysis", "source": {"sha256": "d" * 64},
                 "values": {"analysis_id": RECIPE["id"], "input_sources": [SOURCE]}}
    with pytest.raises(ValueError, match="unperformed"):
        check(evidence=EVIDENCE + [completed])
    different_version = copy.deepcopy(completed)
    different_version["values"]["input_sources"][0] = {**SOURCE, "sha256": "f" * 64}
    assert check(evidence=EVIDENCE + [different_version])["stop_reason"] == "continue"


@pytest.mark.parametrize("case", [None, {"id": "test-case", "source_manifest": []},
                                  {"id": "test-case", "source_manifest": [{**SOURCE, "sha256": "f" * 64}]}])
def test_continuation_does_not_assume_missing_or_changed_source_versions(case):
    with pytest.raises(ValueError, match="qualified source"):
        check(case=case)


def test_stopping_cannot_silently_queue_an_action():
    for changes in ({"next_action_id": RECIPE["id"]}, {"target_hypothesis_ids": ["primary"]},
                    {"continuation_reason": ""}):
        with pytest.raises(ValueError):
            check({**stopped(), **changes})


@pytest.mark.parametrize("field, value", [
    ("statement", "A different hypothesis."),
    ("origin", "agent_generated"),
    ("scope", "A different assay population."),
    ("scope_type", "computational"),
    ("source_quote", "Antigen change explains resistance."),
])
def test_reused_hypothesis_identity_cannot_change(field, value):
    previous = check(stopped())
    changed = stopped()
    changed["hypotheses"][0][field] = value
    with pytest.raises(ValueError):
        check(changed, previous=previous)


def test_previous_hypotheses_cannot_be_silently_removed():
    alternative = entry(hypothesis_id="agent_alt", origin="agent_generated",
                        statement="An additional mechanistic explanation.")
    previous = check(stopped())
    previous["hypotheses"].append(alternative)
    with pytest.raises(ValueError, match="silently dropped"):
        check(stopped(), previous=previous)


def test_rule_out_reopens_only_with_new_accepted_evidence_and_revised_reason():
    previous = check(stopped(excluded(), "resolved_within_scope"))
    reopened = stopped(entry(
        rationale="Reopen the hypothesis because a new qualified measurement contradicts the former exclusion.",
        supporting_evidence_ids=["new-measurement"],
    ))
    new = {"id": "new-measurement", "kind": "measured", "source": {"sha256": "e" * 64}}
    result = check(reopened, previous=previous, evidence=EVIDENCE + [new])
    assert result["hypotheses"][0]["status"] == "possible"
    assert previous["hypotheses"][0]["status"] == "clearly_ruled_out"
    for citation in ("observed", "contradiction"):
        old_only = copy.deepcopy(reopened)
        old_only["hypotheses"][0]["supporting_evidence_ids"] = [citation]
        with pytest.raises(ValueError, match="Reopening"):
            check(old_only, previous=previous)
    reopened["hypotheses"][0]["rationale"] = previous["hypotheses"][0]["rationale"]
    with pytest.raises(ValueError, match="Reopening"):
        check(reopened, previous=previous, evidence=EVIDENCE + [new])


def test_probable_can_be_downgraded_after_reinterpretation_without_fabricating_new_data():
    previous = check(stopped(entry(status="probable")))
    current = stopped(entry(rationale="Reassessment identifies confounding in the same measurement, leaving the mechanism possible."))
    assert check(current, previous=previous)["hypotheses"][0]["status"] == "possible"


@pytest.mark.parametrize("field", ["hypothesis_sha256", "evidence_sha256", "accepted_evidence_versions", "recipe_versions", "interpretation_scope"])
def test_normalized_metadata_tampering_is_rejected(field):
    value = check()
    value[field] = "tampered"
    with pytest.raises(ValueError, match="metadata differs"):
        check(value)


def test_stopping_requires_a_specific_blocker_for_each_unresolved_possible_hypothesis():
    value = stopped(reason="no_informative_action")
    value["hypotheses"][0]["blocker"] = " "
    with pytest.raises(ValueError, match="explicit blocker"):
        check(value)


@pytest.mark.parametrize("status", ["possible", "probable"])
@pytest.mark.parametrize("reason", ["needs_data", "needs_method", "wet_lab_required",
                                    "no_informative_action", "provider_unresolved"])
def test_a_stop_cannot_override_a_ready_unperformed_test_it_explicitly_nominates(status, reason):
    value = stopped(entry(status=status), reason)
    value["hypotheses"][0]["next_analysis_ids"] = [RECIPE["id"]]
    with pytest.raises(ValueError, match="still nominates a ready"):
        check(value)


def test_an_explicitly_input_blocked_followup_allows_an_honest_stop():
    value = stopped(reason="needs_data")
    value["hypotheses"][0]["next_analysis_ids"] = [RECIPE["id"]]
    value["hypotheses"][0]["blocker"] = "The recipe needs the per-sample group assignment before the contrast is valid."
    result = check(value, followups=[{**FOLLOWUP, "status": "needs_inputs"}])
    assert result["stop_reason"] == "needs_data"
    assert result["hypotheses"][0]["status"] == "possible"
    assert result["next_action_id"] is None


@pytest.mark.parametrize("violation", ["drop", "reopen"])
def test_manual_modeling_wrapper_cannot_erase_previous_hypothesis_constraints(violation):
    if violation == "drop":
        previous = check(stopped())
        previous["hypotheses"].append(entry(
            hypothesis_id="prior_alternative", origin="agent_generated",
            statement="A separately tracked alternative remains unresolved.",
            next_analysis_ids=[], blocker="The discriminating assay has not been performed.",
        ))
        current = stopped()
        message = "silently dropped"
    else:
        previous = check(stopped(excluded(), "resolved_within_scope"))
        current = stopped(entry(
            rationale="Reinterpret the old evidence without any new measurement, reopening the former exclusion.",
        ))
        message = "Reopening"
    wrapper = {"governance": None, "prior_governance": previous,
               "summary": "Manual molecular modeling completed without re-running the reviewer ledger."}
    with pytest.raises(ValueError, match=message):
        check(current, previous=wrapper)
