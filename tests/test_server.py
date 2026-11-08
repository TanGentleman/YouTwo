from pathlib import Path

from youtwo.server.server import check_convex_project
from youtwo.server.utils import to_deletions


def test_to_deletions_matches_convex_args():
    observations = [
        {"entityName": "Ada", "contents": ["Writes Rust", "Lives in Paris"]}
    ]
    assert to_deletions(observations) == [
        {"entityName": "Ada", "observations": ["Writes Rust", "Lives in Paris"]}
    ]


def test_check_convex_project(tmp_path):
    assert not check_convex_project(str(tmp_path))
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "convex").mkdir()
    assert check_convex_project(str(tmp_path))
    assert not check_convex_project(str(tmp_path / "missing"))


def test_backend_dir_is_a_convex_project():
    assert check_convex_project(str(Path(__file__).parents[1] / "backend"))
