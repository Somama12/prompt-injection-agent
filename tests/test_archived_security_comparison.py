"""Regression checks for missing evidence, metadata drift and matched pairing."""
import json

import pytest

from evaluation.archived_security_comparison import CONDITIONS, collect, sensitivity


def write_collection(tmp_path):
    (tmp_path / "episodes").mkdir()
    (tmp_path / "manifest.json").write_text(json.dumps({"config": {"model": "test"}}))
    for case in ("__clean__", "case1"):
        for defense in CONDITIONS:
            run_id = f"{defense}__{case}__001"
            metadata = dict(attack_id=case, defense=defense, error="")
            cell = dict(**metadata, model="test", run_id=run_id, trial=1, status="ok",
                        legitimate_success=True, programmatic_success=None if case == "__clean__" else False)
            (tmp_path / "episodes" / (run_id + ".json")).write_text(json.dumps(dict(cell=cell, run=metadata)))
    return tmp_path


def test_empty_collection_rejected(tmp_path):
    (tmp_path / "manifest.json").write_text('{"config": {"model": "test"}}')
    with pytest.raises(ValueError, match="No saved episodes"):
        collect(tmp_path)


def test_incomplete_condition_grid_rejected(tmp_path):
    folder = write_collection(tmp_path)
    (folder / "episodes" / "none__case1__001.json").unlink()
    with pytest.raises(ValueError, match="Unmatched design"):
        collect(folder)


@pytest.mark.parametrize("field,value,message", [
    ("model", "different-model", "model disagrees"),
    ("run_id", "another-case", "identity"),
    ("defense", "unrecognized", "Unknown defense"),
])
def test_inconsistent_identity_rejected(tmp_path, field, value, message):
    folder = write_collection(tmp_path)
    path = folder / "episodes" / "none__case1__001.json"
    record = json.loads(path.read_text())
    record["cell"][field] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match=message):
        collect(folder)


def test_trace_mismatch_rejected(tmp_path):
    folder = write_collection(tmp_path)
    path = folder / "episodes" / "none__case1__001.json"
    record = json.loads(path.read_text())
    record["run"]["attack_id"] = "different-case"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="trace"):
        collect(folder)


def test_matching_exposes_gain_and_loss_hidden_by_equal_totals():
    grid = {}
    for case in ("first", "second"):
        for condition in CONDITIONS:
            success = (case == "first") == (condition == "none")
            grid[case, condition] = dict(category="family", legitimate_success=success, programmatic_success=False)
    result = sensitivity(grid)
    assert result["paired_vs_baseline"]["combined"] == {"gained": ["second"], "lost": ["first"]}
    assert result["by_family"]["family"]["none"]["useful_without_effect"] == 1
    assert result["by_family"]["family"]["combined"]["useful_without_effect"] == 1
    assert result["leave_one_design_out"]["first"]["combined"]["n"] == 1
