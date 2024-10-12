"""Check if source is valid."""

from typing import Any
from typing import Self
from typing import final
from typing import override
from hashlib import sha256
from dataclasses import dataclass
from waydroid_injector.deserializable import Deserializable


@final
@dataclass
class Checksum(Deserializable):
    """Class to describe how to check the source.

    Attributes:
        sha256(str | None): The sha256 checksum.
    """

    sha256: str | None = None

    def check(self, content: bytes) -> bool:
        """Check if the content match the checksums."""
        sha256_match = self.sha256 is None or sha256(content).hexdigest() == self.sha256
        return all([sha256_match])

    @property
    @override
    def valid(self) -> bool:
        return any(i is not None for i in [self.sha256])

    @classmethod
    @override
    def load(cls, data: dict[str, Any]) -> Self:
        sha256_: str | None = data.get("sha256")
        return cls(sha256_)
