"""Install/Uninstall custom contents."""

from os import geteuid
from os import listdir
from typing import Any
from typing import Self
from typing import ClassVar
from typing import final
from typing import override
from logging import getLogger
from pathlib import Path
from dataclasses import field
from dataclasses import dataclass
from configparser import ConfigParser
from waydroid_injector.source import Source
from waydroid_injector.content import Content
from waydroid_injector.deserializable import Deserializable


@final
@dataclass
class _Environment:
    EUID_ROOT = 0
    FALLBACK_CFG: ClassVar[Path] = Path("/var/lib/waydroid/waydroid.cfg")
    FALLBACK_PROP: ClassVar[Path] = Path("/var/lib/waydroid/waydroid.prop")

    waydroid: Path
    overlay: Path
    overlay_rw: Path
    user_data: Path
    cfg: Path

    @classmethod
    def ensure_environment(cls, dry_run: bool, destdir: Path | None) -> Self:
        if not dry_run and geteuid() != cls.EUID_ROOT:
            raise PermissionError("Root permission is required.")
        slash = destdir or Path("/")
        waydroid = slash / "var/lib/waydroid"
        overlay = waydroid / "overlay"
        overlay_rw = waydroid / "overlay_rw"
        cfg = waydroid / "waydroid.cfg"
        prop = waydroid / "waydroid.prop"

        parser = ConfigParser()
        _ = parser.read(cfg if cfg.is_file() else cls.FALLBACK_CFG)
        if not parser.getboolean("waydroid", "mount_overlays"):
            raise ValueError("waydroid.mount_overlays should be True in {}".format(cfg))
        prop_dict = dict(
            line.split("=", 1)
            for line in (prop if prop.is_file() else cls.FALLBACK_PROP)
            .read_text()
            .splitlines()
        )
        user_data = slash / Path(prop_dict["waydroid.host_data_path"]).relative_to("/")
        return cls(waydroid, overlay, overlay_rw, user_data, cfg)


@final
@dataclass
class Manifest(Deserializable):
    """Class to describe how to install contents into waydroid's data.

    Attributes:
        name(str): The name of the manifest.
        version(str): The version of the manifest.
        set_property(dict[str, str]): Properties to be set in waydroid's data.
        sources(list[Source]): Contents need to be obtained before installing.
        contents(list[Content]): Contents need to be placed into waydroid's data.
    """

    name: str
    version: str
    set_property: dict[str, str] = field(default_factory=dict)
    sources: list[Source] = field(default_factory=list)
    contents: list[Content] = field(default_factory=list)

    def install(self, dry_run: bool, destdir: Path | None):
        """Install the manifest.

        Args:
            dry_run(bool): If in dry-run mode.
            destdir(Path | None): Where is the /, Use / if is None.
        """
        logger = getLogger(__name__)
        logger.info("Installing %s version %s...", self.name, self.version)
        environment = _Environment.ensure_environment(dry_run, destdir)

        srcdir = (
            environment.waydroid
            / "injector"
            / "{name}-{version}".format(name=self.name, version=self.version)
        )
        srcdir.mkdir(parents=True, exist_ok=True)
        for source in self.sources:
            source.get(srcdir, self.name, self.version)
            source.do_build(srcdir, self.name, self.version)

        for content in self.contents:
            content.create(
                srcdir,
                self.name,
                self.version,
                environment.overlay,
                environment.overlay_rw,
                environment.user_data,
            )

        for source in self.sources:
            source.cleanup(srcdir, self.name, self.version)

        parser = ConfigParser()
        if environment.cfg.is_file():
            _ = parser.read(environment.cfg)
        for key, value in self.set_property.items():
            logger.debug("Setting property %s to %s...", key, value)
            parser.set("properties", key, value)

        with environment.cfg.open("w") as writer:
            parser.write(writer)

        self.__post_operation()

    def uninstall(self, dry_run: bool, destdir: Path | None):
        """Uninstall the manifest.

        Args:
            dry_run(bool): If in dry-run mode.
            destdir(Path | None): Where is the /, Use / if is None.
        """
        logger = getLogger(__name__)
        logger.info("Removing %s version %s...", self.name, self.version)
        environment = _Environment.ensure_environment(dry_run, destdir)

        contents = self.contents.copy()
        contents.reverse()
        for content in contents:
            content.remove(
                environment.overlay,
                environment.overlay_rw,
                environment.user_data,
            )

        partitions = ["system", "vendor"]
        overlay_keeps = [environment.overlay / partition for partition in partitions]
        _ = self.__clean(environment.overlay, overlay_keeps)
        if environment.overlay_rw.is_dir():
            overlay_rw_keeps = [
                environment.overlay_rw / partition for partition in partitions
            ]
            _ = self.__clean(environment.overlay_rw, overlay_rw_keeps)

        parser = ConfigParser()
        if environment.cfg.exists():
            _ = parser.read(environment.cfg)
        for key, value in self.set_property.items():
            logger.debug("Removing property %s with value %s...", key, value)
            if (
                parser.has_option("properties", key)
                and parser.get("properties", key) == value
            ):
                _ = parser.remove_option("properties", key)

        with environment.cfg.open("w") as writer:
            parser.write(writer)

        self.__post_operation()

    def __clean(self, path: Path, keeps: list[Path]) -> bool:
        logger = getLogger(__name__)
        if path.is_dir() and all(keep.is_relative_to(path) for keep in keeps):
            for item in listdir(path):
                p = path / item
                if p.is_dir():
                    keeps_for_p = [
                        keep for keep in keeps if keep != p and keep.is_relative_to(p)
                    ]
                    if self.__clean(p, keeps_for_p) and p not in keeps:
                        logger.debug("Removing %s...", p)
                        p.rmdir()
        return len(listdir(path)) == 0

    def __post_operation(self):
        logger = getLogger(__name__)
        if len(self.set_property) > 0:
            logger.info(
                (
                    "Please run `waydroid upgrade` or `waydroid init --force`",
                    " to let your custom property being applied correctly.",
                ),
            )

    @property
    @override
    def valid(self) -> bool:
        return self.name != "" and self.version != "" and len(self.contents) > 0

    @classmethod
    @override
    def load(cls, data: dict[str, Any]) -> Self:
        name: str | None = data.get("name")
        if name is None:
            raise ValueError("Manifest.name should not be None.")
        version = data.get("version")
        if version is None:
            raise ValueError("Manifest.version should not be None.")
        set_property: dict[str, str] = data.get("set-property", {})
        sources: list[Source] = [Source.load(i) for i in data.get("sources", [])]  # pyright: ignore[reportAny]
        contents: list[Content] = [Content.load(i) for i in data.get("contents", [])]  # pyright: ignore[reportAny]
        return cls(name, version, set_property, sources, contents)  # pyright: ignore[reportAny]
