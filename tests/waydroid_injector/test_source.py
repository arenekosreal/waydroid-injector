"""Test src/waydroid_injector/source.py."""

# pyright: reportAny=false

import pytest
from typing import Any
from typing import ClassVar
from pathlib import Path
from waydroid_injector.source import Source


class TestSource:
    """Test Source class."""

    _INVALID_SOURCE_JSON_NO_SOURCE: ClassVar[dict[str, Any]] = {}
    _VALID_SOURCE_JSON_URL: ClassVar[dict[str, Any]] = {
        "url": "https://example.com/file.bin",
    }
    _INVALID_SOURCE_JSON_PATH: ClassVar[dict[str, Any]] = {"path": "/path/to/test"}
    _VALID_SOURCE_JSON_PATH: ClassVar[dict[str, Any]] = {"path": "/usr/bin"}
    _VALID_SOURCE_JSON_FILE_NAME: ClassVar[dict[str, Any]] = {
        "url": "https://example.com/file.bin",
        "file-name": "test.bin",
    }

    @pytest.fixture
    def srcdir(self, tmp_path: Path) -> Path:
        """Generate a srcdir for Source testing."""
        p = tmp_path / "src"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def test_get(self, tmp_path: Path, srcdir: Path):
        """Test Source.get function."""
        source_json = {"path": str(tmp_path / "test")}
        source = Source.load(source_json)
        path = source_json["path"]
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch(exist_ok=True)
        source.get(srcdir, "test", "1.0")
        f = srcdir / "test"
        assert f.exists()

    def test_do_build(self, tmp_path: Path, srcdir: Path):
        """Test Source.do_build function."""
        source_json = {
            "path": str(tmp_path / "test"),
            "build": {"cmd": ["touch", "build"]},
        }
        source = Source.load(source_json)
        source.do_build(srcdir, "test", "1.0")
        assert (srcdir / "build").is_file()

    def test_cleanup(self, srcdir: Path):
        """Test Source.cleanup function."""
        remove = srcdir / "remove"
        exist = srcdir / "exist"
        remove.touch()
        exist.touch()
        source_json = {"path": "/path/not/exist"}
        source = Source.load(source_json)
        source.cleanup(srcdir, "test", "1.0")
        assert not remove.exists()
        assert exist.exists()

    @pytest.mark.parametrize(
        ("data", "valid"),
        [
            (_INVALID_SOURCE_JSON_NO_SOURCE, False),
            (_VALID_SOURCE_JSON_FILE_NAME, True),
            (_INVALID_SOURCE_JSON_PATH, False),
            (_VALID_SOURCE_JSON_PATH, True),
            (_VALID_SOURCE_JSON_URL, True),
        ],
    )
    def test_valid(self, data: dict[str, Any], valid: bool):
        """Test Source.valid property."""
        source = Source.load(data)
        assert source.valid == valid

    def test_load(self):
        """Test Source.load function."""
        source = Source.load(self._VALID_SOURCE_JSON_URL)
        assert source.url == self._VALID_SOURCE_JSON_URL["url"]
