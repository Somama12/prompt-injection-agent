"""Compare frozen outcomes for matched full-agent Groq cases. No API calls."""
from collections import Counter
from pathlib import Path
import json

from evaluation.archived_findings import CONDITIONS, EVIDENCE, digest, read, require


def collect(folder):
    manifest = read(folder / "manifest.json")["config"]
    grid, excluded, hashes = {}, [], {}
    paths = sorted((folder / "episodes").glob("*.json"))
    require(bool(paths), f"No saved episodes in {folder}")
    for path in paths:
        record = read(path)
        cell = record["cell"]
        run = record["run"]
        hashes[path.name] = digest(path.read_bytes())
        require(cell["run_id"] == path.stem, "Episode filename disagrees with its identity")
        require(cell["defense"] in CONDITIONS, "Unknown defense condition")
        require(cell["model"] == manifest["model"], "Episode model disagrees with manifest")
        require(all(cell[key] == run[key] for key in ("attack_id", "defense", "error")),
                "Episode metadata disagrees with its trace")
        if cell["error"]:
            excluded.append(path.stem)
            continue
        key = cell["attack_id"], cell["defense"]
        require(key not in grid and cell["trial"] == 1 and cell["status"] == "ok", "Unexpected trial or status")
        require(type(cell["legitimate_success"]) is bool, "Missing task outcome")
        if key[0] != "__clean__":
            require(type(cell["programmatic_success"]) is bool, "Missing security outcome")
        grid[key] = cell
    cases = {a for a,d in grid}
    require("__clean__" in cases and len(cases) > 1, "Missing controls or attacked designs")
    require(all({d for a,d in grid if a == case} == CONDITIONS for case in cases), "Unmatched design")
    hashes["../manifest.json"] = digest((folder / "manifest.json").read_bytes())
    return manifest, grid, dict(terminal_errors=excluded, file_hashes=hashes)


def outcomes(grid):
    cases = sorted({a for a,d in grid} - {"__clean__"})
    result = {}
    for condition in sorted(CONDITIONS):
        cells = [grid[a,condition] for a in cases]
        hits = sum(c["programmatic_success"] for c in cells)
        useful = sum(c["legitimate_success"] and not c["programmatic_success"] for c in cells)
        result[condition] = dict(n=len(cells), assigned_effect=hits, useful_without_effect=useful)
    return result


def sensitivity(grid):
    """Describe pairing and case composition without treating repeats as new designs."""
    cases = sorted({case for case, _ in grid} - {"__clean__"})
    rows = []
    families = {}
    for case in cases:
        category = grid[case, "none"]["category"]
        families[case] = category
        for condition in sorted(CONDITIONS):
            cell = grid[case, condition]
            require(cell["category"] == category, "Inconsistent category for a design")
            rows.append(dict(case=case, family=category, condition=condition,
                             assigned_effect=cell["programmatic_success"],
                             task=cell["legitimate_success"],
                             useful_without_effect=cell["legitimate_success"] and not cell["programmatic_success"]))
    comparisons = {}
    for condition in sorted(CONDITIONS):
        gained, lost = [], []
        for case in cases:
            baseline = grid[case, "none"]
            treated = grid[case, condition]
            before = baseline["legitimate_success"] and not baseline["programmatic_success"]
            after = treated["legitimate_success"] and not treated["programmatic_success"]
            if after and not before:
                gained.append(case)
            if before and not after:
                lost.append(case)
        comparisons[condition] = dict(gained=gained, lost=lost)
    by_family = {}
    for family in sorted(set(families.values())):
        subset = {key: cell for key, cell in grid.items() if families.get(key[0]) == family}
        by_family[family] = outcomes(subset)
    leave_one_out = {}
    for omitted in cases:
        subset = {key: cell for key, cell in grid.items() if key[0] != omitted}
        leave_one_out[omitted] = outcomes(subset)
    return dict(rows=rows, paired_vs_baseline=comparisons, by_family=by_family,
                leave_one_design_out=leave_one_out)


def compare():
    m1, pilot, p = collect(Path("results/groq_pilot_v3"))
    m2, extended, e = collect(Path("results/groq_full_three_trials"))
    different = sorted(k for k in m1.keys() | m2.keys() if m1.get(k) != m2.get(k))
    require(set(different) <= {"attacks","repeats","rpm"}, "Incompatible configuration")
    first = extended | pilot
    second = pilot | extended
    ids = {a for a,d in first} - {"__clean__"}
    shared = sorted({a for a,d in pilot.keys() & extended.keys()} - {"__clean__"})
    families = Counter(next(c["category"] for (a,d),c in first.items() if a == case) for case in ids)
    clean = {name:sum(c["legitimate_success"] for (a,d),c in grid.items() if a == "__clean__")
             for name,grid in [("pilot",pilot),("interrupted_collection",extended)]}
    return dict(model=m1["model"], config_differences=different, design_count=len(ids), families=dict(families),
                shared_designs=shared, pilot=outcomes(pilot), interrupted_collection=outcomes(extended),
                pilot_priority=outcomes(first), interrupted_priority=outcomes(second), clean_successes=clean,
                sensitivity=sensitivity(first), provenance=dict(pilot=p,interrupted_collection=e))


if __name__ == "__main__":
    path = EVIDENCE / "archived_security_comparison.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(compare(), indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
