"""Tests for the propositional logic answers (Questions 2, 3 and 4)."""

import json
import os

import pytest

from logic.propositional import (TRUE, classify, clauses_of, count_models, parse,
                                 pl_resolution, pl_true, to_cnf, truth_table,
                                 tt_entails, is_valid_by_resolution)

with open(os.path.join(os.path.dirname(__file__), "data", "logic_cases.json")) as f:
    CASES = json.load(f)


@pytest.mark.parametrize("case", CASES["classify"], ids=lambda c: c["id"])
def test_classification_by_truth_table(case):
    assert classify(case["sentence"]) == case["expected"]


@pytest.mark.parametrize("case", CASES["classify"], ids=lambda c: c["id"])
def test_validity_agrees_with_resolution(case):
    assert is_valid_by_resolution(case["sentence"]) == (case["expected"] == "valid")


@pytest.mark.parametrize("case", CASES["classify"], ids=lambda c: c["id"])
def test_validity_agrees_with_tt_entails(case):
    assert tt_entails("True", case["sentence"]) == (case["expected"] == "valid")


@pytest.mark.parametrize("case", CASES["models"], ids=lambda c: c["id"])
def test_model_counts(case):
    assert count_models(case["sentence"], case["vocabulary"]) == case["expected"]


@pytest.mark.parametrize("case", CASES["cnf"], ids=lambda c: c["id"])
def test_cnf_is_equivalent_and_gives_expected_clauses(case):
    s = parse(case["sentence"])
    cnf = to_cnf(s)
    for model, value in truth_table(s):
        assert pl_true(cnf, model) == value
    expected = {frozenset(c) for c in case["clauses"]}
    assert clauses_of(s) == expected


def test_parser_precedence():
    # ~ binds tighter than &, & tighter than |, | tighter than ==>
    s = parse("~A & B | C ==> D")
    assert repr(s) == "((~A & B) | C) ==> D"


def test_resolution_entailment_examples():
    # Wumpus world style: from P and P ==> Q we get Q but not ~Q
    assert pl_resolution(parse("P & (P ==> Q)"), parse("Q"))
    assert not pl_resolution(parse("P & (P ==> Q)"), parse("~Q"))
    assert not pl_resolution(TRUE, parse("Smoke ==> Fire"))
