"""Build a source."""

from typing import Any
from typing import Self
from typing import final
from typing import override
from logging import getLogger
from pathlib import Path
from subprocess import run
from dataclasses import field
from dataclasses import dataclass
from waydroid_injector.deserializable import Deserializable


@final
@dataclass
class Build(Deserializable):
    """Class to describe how to build the source.

    Attributes:
        cmd(list[str]): The command in list to be run, like ["ls", "-l"].
        shell(str | None): A shell script to be run. Defaults to None.

    Remarks:
        Must ensure cmd is not empty or shell is not None.
        Or nothing will happen when calls build() function.
    """

    cmd: list[str] = field(default_factory=list)
    shell: str | None = None

    def build(self, srcdir: Path, file_name: str):
        """Build the source.

        Args:
            srcdir(Path): Where the source contents are storaged.
            file_name(str): The file-name value in manifest.
        """
        logger = getLogger(__name__)
        default_path = [
            "/bin",
            "/sbin",
            "/usr/bin",
            "/usr/sbin",
            "/usr/local/bin",
            "/usr/local/sbin",
        ]
        env = {"PATH": ":".join(default_path)}
        if len(self.cmd) > 0:
            cmd = [i.format(srcdir=srcdir, file_name=file_name) for i in self.cmd]
            logger.debug("Invoking command %s", cmd)
            _ = run(cmd, cwd=srcdir, check=True, env=env)  # noqa: S603
        elif self.shell is not None:
            shell = self.shell.format(srcdir=srcdir, file_name=file_name)
            logger.debug("Running script in shell...")
            logger.debug("Script: %s", shell)
            _ = run(shell, shell=True, check=True, env=env)  # noqa: S602

    @property
    @override
    def valid(self) -> bool:
        has_cmd = len(self.cmd) > 0
        has_shell = self.shell is not None
        return any([has_cmd, has_shell])

    @classmethod
    @override
    def load(cls, data: dict[str, Any]) -> Self:
        cmd: list[str] | None = data.get("cmd")
        shell: str | None = data.get("shell")
        return cls(cmd or [], shell)
