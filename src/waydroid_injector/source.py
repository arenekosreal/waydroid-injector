"""Obtain content for Manifest."""

from shutil import copy2
from typing import Any
from typing import Self
from typing import final
from typing import override
from logging import getLogger
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import urlopen
from waydroid_injector.build import Build
from waydroid_injector.checksum import Checksum
from waydroid_injector.deserializable import Deserializable


@final
@dataclass
class Source(Deserializable):
    """Class to describe how to prepare contents required by the manifest.

    Attributes:
        file_name(str | None): The file-name in manifest.sources.
        Use calculated file name if it is None.

        checksum(Checksum | None): The checksum in manifest.sources.
        None is not recommended as there will be no check for source.

        build(Build |None): The build in manifest.sources.
        None means there is no need to build the source.

        url(str | None): The url to the source.
        Only http/https/ftp protocol is accepted.

        path(Path | None): The path to the source.

    Remarks:
        One of url and path must not be None.
    """

    file_name: str | None
    checksum: Checksum | None
    build: Build | None
    url: str | None = None
    path: Path | None = None

    def get(self, srcdir: Path, name: str, version: str):
        """Get the source and build it.

        Args:
            srcdir(Path): Where the source contents are storaged.
            name(str): The name in manifest.
            version(str): The version in manifest.
        """
        logger = getLogger(__name__)
        allowed_url_schemes = ("http:", "https:", "ftp:")
        url = (
            self.url.format(name=name, version=version)
            if self.url is not None
            else None
        )

        path = (
            Path(str(self.path).format(name=name, version=version))
            if self.path is not None
            else None
        )
        default_file_name = (
            Path(urlparse(url).path).name
            if url is not None
            else path.name
            if path is not None
            else None
        )
        file_name = (
            self.file_name.format(name=name, version=version)
            if self.file_name is not None
            else default_file_name
        )
        if file_name is None:
            raise ValueError("Failed to get proper file name to save content.")

        dst = srcdir / file_name
        obtain = True
        if dst.is_file():
            if self.checksum is not None:
                if self.checksum.check(dst.read_bytes()):
                    logger.info("Checksum match.")
                    obtain = False
                else:
                    logger.error("Checksum mismatch.")
                    dst.unlink()
            else:
                logger.warning("No Checksum is set.")
                obtain = False
            logger.info("Found required source, skipping obtaining...")

        if obtain:
            if path is not None:
                logger.info("Obtaining %s from %s", file_name, path)
                copy2(path, dst)
            elif url is not None and url.startswith(allowed_url_schemes):
                logger.info("Obtaining %s from %s", file_name, url)
                with urlopen(url) as resp:  # noqa: S310 # pyright: ignore[reportAny]
                    _ = dst.write_bytes(resp.read())  # pyright: ignore[reportAny]
            else:
                raise RuntimeError("Does not know how to obtain this source.")
            if self.checksum is not None and not self.checksum.check(dst.read_bytes()):
                raise RuntimeError("Checksum mismatch.")

        if self.build is not None:
            self.build.build(srcdir, file_name)

    @property
    @override
    def valid(self) -> bool:
        return self.url is not None or (self.path is not None and self.path.exists())

    @classmethod
    @override
    def load(cls, data: dict[str, Any]) -> Self:
        file_name: str | None = data.get("file-name")
        checksum_dict = data.get("checksum")
        checksum = Checksum.load(checksum_dict) if checksum_dict is not None else None  # pyright: ignore[reportAny]
        if checksum is not None and not checksum.valid:
            raise ValueError("Checksum is not valid.")
        build_dict = data.get("build")
        build = Build.load(build_dict) if build_dict is not None else None  # pyright: ignore[reportAny]
        if build is not None and not build.valid:
            raise ValueError("Build is not valid.")
        url: str | None = data.get("url")
        path_str: str | None = data.get("path")
        path = Path(path_str) if path_str is not None else None
        return cls(file_name, checksum, build, url, path)
