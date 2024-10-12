"""Install/Uninstall custom contents."""

from os import geteuid
from typing import Any
from typing import Self
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
        euid_root = 0
        fallback_cfg = Path("/var/lib/waydroid/waydroid.cfg")
        fallback_prop = Path("/var/lib/waydroid/waydroid.prop")
        slash = destdir if destdir is not None else Path("/")
        waydroid = slash / "var/lib/waydroid"
        overlay = waydroid / "overlay"
        overlay_rw = waydroid / "overlay_rw"
        cfg = waydroid / "waydroid.cfg"
        prop = waydroid / "waydroid.prop"
        parser = ConfigParser()
        _ = parser.read(cfg if cfg.is_file() else fallback_cfg)
        if not dry_run and geteuid() != euid_root:
            raise PermissionError("Root permission is required.")
        if not parser.getboolean("waydroid", "mount_overlays"):
            raise ValueError("waydroid.mount_overlays should be True in {}".format(cfg))

        prop_dict = dict(
            line.split("=", 1)
            for line in (prop if prop.is_file() else fallback_prop)
            .read_text()
            .splitlines()
        )
        user_data = slash / Path(prop_dict["waydroid.host_data_path"]).relative_to("/")

        srcdir = (
            waydroid
            / "injector"
            / "{name}-{version}".format(name=self.name, version=self.version)
        )
        for source in self.sources:
            srcdir.mkdir(parents=True, exist_ok=True)
            source.get(srcdir, self.name, self.version)

        for content in self.contents:
            content.create(
                srcdir,
                self.name,
                self.version,
                overlay,
                overlay_rw,
                user_data,
            )

        for key, value in self.set_property.items():
            logger.debug("Setting property %s to %s...", key, value)
            parser.set("properties", key, value)

        with cfg.open("w") as writer:
            parser.write(writer)

    def uninstall(self, dry_run: bool, destdir: Path | None):
        """Uninstall the manifest.

        Args:
            dry_run(bool): If in dry-run mode.
            destdir(Path | None): Where is the /, Use / if is None.
        """
        logger = getLogger(__name__)
        logger.info("Removing %s version %s...", self.name, self.version)
        euid_root = 0
        fallback_cfg = Path("/var/lib/waydroid/waydroid.cfg")
        fallback_prop = Path("/var/lib/waydroid/waydroid.prop")
        slash = destdir if destdir is not None else Path("/")
        waydroid = slash / "var/lib/waydroid"
        overlay = waydroid / "overlay"
        overlay_rw = waydroid / "overlay_rw"
        cfg = waydroid / "waydroid.cfg"
        prop = waydroid / "waydroid.prop"
        parser = ConfigParser()
        _ = parser.read(cfg if cfg.is_file() else fallback_cfg)
        if not dry_run and geteuid() != euid_root:
            raise PermissionError("Root permission is required.")
        if not parser.getboolean("waydroid", "mount_overlays"):
            raise ValueError("waydroid.mount_overlays should be True in {}".format(cfg))

        prop_dict = dict(
            line.split("=", 1)
            for line in (prop if prop.is_file() else fallback_prop)
            .read_text()
            .splitlines()
        )
        user_data = slash / Path(prop_dict["waydroid.host_data_path"]).relative_to("/")

        for content in self.contents:
            content.remove(overlay, overlay_rw, user_data)

        for key, value in self.set_property.items():
            logger.debug("Removing property %s with value %s...", key, value)
            if (
                parser.has_option("properties", key)
                and parser.get("properties", key) == value
            ):
                _ = parser.remove_option("properties", key)

        with cfg.open("w") as writer:
            parser.write(writer)

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
