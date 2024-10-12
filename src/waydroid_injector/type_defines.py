"""Types of waydroid_injector."""

from typing import Literal
from typing import Callable
from pathlib import Path


type ContentType = Literal["directory", "file", "link"]
type CompressType = Literal["gz"]
type EntrypointFunctionType = Callable[[bool, Path], None]
