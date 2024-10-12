"""Test src/waydroid_injector/checksum.py."""

import pytest
from os import urandom
from typing import Any
from typing import ClassVar
from hashlib import sha256
from waydroid_injector.checksum import Checksum


class TestChecksum:
    """Test Checksum class."""

    _VALID_CHECKSUM_JSON: ClassVar[dict[str, str | None]] = {
        "sha256": "example-sha-256",
    }
    _INVALID_CHECKSUM_NONE_JSON: ClassVar[dict[str, str | None]] = {"sha256": None}
    _INVALID_CHECKSUM_EMPTY_JSON: ClassVar[dict[str, str | None]] = {}

    def test_check(self):
        """Test Checksum.check function."""
        content_size = 42
        content = urandom(content_size)
        hexdigest = sha256(content).hexdigest()
        checksum = Checksum.load({"sha256": hexdigest})
        assert checksum.check(content)

    @pytest.mark.parametrize(
        ("data", "valid"),
        [
            (_VALID_CHECKSUM_JSON, True),
            (_INVALID_CHECKSUM_EMPTY_JSON, False),
            (_INVALID_CHECKSUM_NONE_JSON, False),
        ],
    )
    def test_valid(self, data: dict[str, Any], valid: bool):
        """Test Checksum.valid property."""
        checksum = Checksum.load(data)
        assert checksum.valid == valid

    def test_load(self):
        """Test Checksum.load function."""
        checksum = Checksum.load(self._VALID_CHECKSUM_JSON)
        assert checksum.sha256 == self._VALID_CHECKSUM_JSON["sha256"]
