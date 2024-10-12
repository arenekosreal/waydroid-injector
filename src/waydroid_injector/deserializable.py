"""Basic deserializable object."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Self


class Deserializable(ABC):
    """Basic class which can be deserialized from dict[str, Any]."""

    @property
    @abstractmethod
    def valid(self) -> bool:
        """If it is valid to be used."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(cls, data: dict[str, Any]) -> Self:
        """Create instance from dict[str, Any].

        Remarks:
            Use this method to create instance
            instead initializing from constructor is prefered.
        """
        raise NotImplementedError
