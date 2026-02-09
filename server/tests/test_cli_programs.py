from __future__ import annotations

from interview.cli.programs import get_default_path


class TestGetDefaultPath:
    def test_returns_path_under_data_optimized(self) -> None:
        path = get_default_path("interview_step")
        assert path.name == "interview_step.json"
        assert "data" in path.parts
        assert "optimized" in path.parts

    def test_different_modules_get_different_paths(self) -> None:
        p1 = get_default_path("interview_step")
        p2 = get_default_path("text_extractor")
        assert p1 != p2
        assert p1.stem == "interview_step"
        assert p2.stem == "text_extractor"
