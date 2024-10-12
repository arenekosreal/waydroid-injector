"""Test src/waydroid_injector/build.py."""

# pyright: reportUnknownArgumentType=false

import pytest
from typing import Any
from typing import ClassVar
from pathlib import Path
from waydroid_injector.build import Build


class TestBuild:
    """Test Build class."""

    _VALID_BUILD_CMD_JSON: ClassVar[dict[str, list[str]]] = {"cmd": ["ls", "-l"]}
    _VALID_BUILD_SHELL_JSON: ClassVar[dict[str, str]] = {"shell": "ls -l"}
    _INVALID_BUILD_JSON: ClassVar[dict[str, Any]] = {}

    def test_build(self, tmp_path: Path):
        """Test Build.build function."""
        build = Build.load(self._VALID_BUILD_CMD_JSON)
        build.build(tmp_path, "pytest")

    @pytest.mark.parametrize(
        ("data", "valid"),
        [
            (_VALID_BUILD_CMD_JSON, True),
            (_VALID_BUILD_SHELL_JSON, True),
            (_INVALID_BUILD_JSON, False),
        ],
    )
    def test_valid(self, data: dict[str, Any], valid: bool):
        """Test Build.valid property."""
        build = Build.load(data)
        assert build.valid == valid

    def test_load(self):
        """Test Build.load function."""
        build = Build.load(self._VALID_BUILD_CMD_JSON)
        assert build.cmd == self._VALID_BUILD_CMD_JSON["cmd"]
