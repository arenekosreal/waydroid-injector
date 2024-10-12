"""Test src/waydroid_injector/manifest.py."""

import pytest
from typing import Any
from typing import ClassVar
from pathlib import Path
from configparser import ConfigParser
from waydroid_injector.manifest import Manifest


@pytest.fixture
def destdir(tmp_path: Path) -> Path:
    """Get a destdir to test install/uninstall.

    Returns:
        Path: The destdir.
    """
    waydroid = tmp_path / "var/lib/waydroid"
    waydroid.mkdir(parents=True, exist_ok=True)
    parser = ConfigParser()
    parser["waydroid"] = {"mount_overlays": "True"}
    cfg = waydroid / "waydroid.cfg"
    with cfg.open("w") as writer:
        parser.write(writer)
    prop = waydroid / "waydroid.prop"
    _ = prop.write_text(
        "waydroid.host_data_path={tmp_path}/userdata".format(tmp_path=tmp_path),
    )
    return tmp_path


class TestManifest:
    """Test Manifest class."""

    _VALID_MANIFEST: ClassVar[dict[str, Any]] = {
        "name": "test",
        "version": "1.0",
        "set-property": {},
        "sources": [],
        "contents": [
            {
                "path": "{overlay}/test",
                "type": "file",
            },
        ],
    }
    _INVALID_MANIFEST_NO_NAME: ClassVar[dict[str, Any]] = {
        "version": "1.0",
        "set-property": {},
        "sources": [],
        "contents": [
            {
                "path": "{overlay}/test",
                "type": "file",
            },
        ],
    }
    _INVALID_MANIFEST_NO_VERSION: ClassVar[dict[str, Any]] = {
        "name": "test",
        "set-property": {},
        "sources": [],
        "contents": [
            {
                "path": "{overlay}/test",
                "type": "file",
            },
        ],
    }
    _INVALID_MANIFEST_NO_CONTENT: ClassVar[dict[str, Any]] = {
        "name": "test",
        "version": "1.0",
        "set-property": {},
        "sources": [],
        "contents": [],
    }

    def test_install(self, destdir: Path):
        """Test Manifest.install function."""
        manifest = Manifest.load(self._VALID_MANIFEST)
        manifest.install(True, destdir)
        p = destdir / "var/lib/waydroid/overlay"
        p.mkdir(parents=True, exist_ok=True)
        target = p / "test"
        assert target.is_file()

    def test_uninstall(self, destdir: Path):
        """Test Manifest.uninstall function."""
        p = destdir / "var/lib/waydroid/overlay/test"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
        manifest = Manifest.load(self._VALID_MANIFEST)
        manifest.uninstall(True, destdir)
        assert not p.exists()

    @pytest.mark.parametrize(
        ("data", "valid"),
        [
            (_VALID_MANIFEST, True),
            (_INVALID_MANIFEST_NO_CONTENT, False),
        ],
    )
    def test_valid(self, data: dict[str, Any], valid: bool):
        """Test Manifest.valid property."""
        manifest = Manifest.load(data)
        assert manifest.valid == valid

    @pytest.mark.parametrize(
        "data",
        [
            _INVALID_MANIFEST_NO_NAME,
            _INVALID_MANIFEST_NO_VERSION,
        ],
    )
    def test_load_invalid(self, data: dict[str, Any]):
        """Test Manifest.load function with invalid inputs."""
        with pytest.raises(ValueError, match="Manifest.*"):
            _ = Manifest.load(data)

    @pytest.mark.parametrize(
        "data",
        [
            _VALID_MANIFEST,
        ],
    )
    def test_load_valid(self, data: dict[str, Any]):
        """Test Manifest.load function with valid inputs."""
        manifest = Manifest.load(data)
        assert manifest.name == data["name"]
        assert manifest.version == data["version"]
