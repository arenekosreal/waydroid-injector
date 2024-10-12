"""Test src/waydroid_injector/content.py."""

# pyright: reportAny=false

import pytest
from typing import Any
from typing import ClassVar
from pathlib import Path
from waydroid_injector.content import Content


class TestContent:
    """Test Content class."""

    _VALID_CONTENT_JSON_NO_MODE_OVERRIDE: ClassVar[dict[str, Any]] = {
        "path": "{overlay}/test",
        "type": "file",
        "content": "test",
    }
    _VALID_CONTENT_JSON: ClassVar[dict[str, Any]] = {
        "path": "{overlay}/test",
        "type": "file",
        "mode": 0o755,
        "content": "test",
    }
    _INVALID_CONTENT_JSON_FILE_MISSING_CONTENT: ClassVar[dict[str, Any]] = {
        "path": "{overlay}/test",
        "type": "file",
    }
    _INVALID_CONTENT_JSON_NONE: ClassVar[dict[str, Any]] = {}
    _INVALID_CONTENT_JSON_MISSING_PATH: ClassVar[dict[str, Any]] = {"type": "file"}
    _INVALID_CONTENT_JSON_MISSING_TYPE: ClassVar[dict[str, Any]] = {
        "path": "{overlay}/test",
    }

    @pytest.mark.parametrize(
        ("data", "mode"),
        [
            (_VALID_CONTENT_JSON_NO_MODE_OVERRIDE, 0o644),
            (_VALID_CONTENT_JSON, 0o755),
        ],
    )
    def test_mode(self, data: dict[str, Any], mode: int):
        """Test Content.mode property."""
        content = Content.load(data)
        assert content.mode == mode

    def test_create(self, tmp_path: Path):
        """Test Content.create function."""
        content = Content.load(self._VALID_CONTENT_JSON)
        content.create(
            tmp_path / "src",
            "test",
            "1.0",
            tmp_path / "overlay",
            tmp_path / "overlay_rw",
            tmp_path / "userdata",
        )
        formatted_path = self._VALID_CONTENT_JSON["path"].format(
            overlay=tmp_path / "overlay",
            overlay_rw=tmp_path / "overlay_rw",
            user_data=tmp_path / "userdata",
        )
        p = Path(formatted_path)
        assert p.exists()
        assert p.stat().st_mode & 0o777 == content.mode

    def test_remove(self, tmp_path: Path):
        """Test Content.remove function."""
        formatted_path = self._VALID_CONTENT_JSON["path"].format(
            overlay=tmp_path / "overlay",
            overlay_rw=tmp_path / "overlay_rw",
            user_data=tmp_path / "userdata",
        )
        p = Path(formatted_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch(exist_ok=True)
        content = Content.load(self._VALID_CONTENT_JSON)
        content.remove(
            tmp_path / "overlay",
            tmp_path / "overlay_rw",
            tmp_path / "userdata",
        )
        assert not p.exists()

    @pytest.mark.parametrize(
        "data",
        [
            (_VALID_CONTENT_JSON),
            (_VALID_CONTENT_JSON_NO_MODE_OVERRIDE),
        ],
    )
    def test_valid(self, data: dict[str, Any]):
        """Test Content.valid property."""
        content = Content.load(data)
        assert content.valid

    @pytest.mark.parametrize(
        "data",
        [
            _VALID_CONTENT_JSON,
            _VALID_CONTENT_JSON_NO_MODE_OVERRIDE,
        ],
    )
    def test_load_valid(self, data: dict[str, Any]):
        """Test Content.load function with valid inputs."""
        _ = Content.load(data)

    @pytest.mark.parametrize(
        "data",
        [
            _INVALID_CONTENT_JSON_MISSING_PATH,
            _INVALID_CONTENT_JSON_MISSING_TYPE,
            _INVALID_CONTENT_JSON_NONE,
        ],
    )
    def test_load_invalid(self, data: dict[str, Any]):
        """Test Content.load function with invalid inputs."""
        with pytest.raises(ValueError, match="Content.*"):
            _ = Content.load(data)

    @pytest.mark.parametrize("data", [_INVALID_CONTENT_JSON_FILE_MISSING_CONTENT])
    def test_load_invalid_no_raises(self, data: dict[str, Any]):
        """Test Content.load funciton with invalid inputs."""
        content = Content.load(data)
        assert not content.valid
