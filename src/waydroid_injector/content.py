"""A content to be created/removed."""

from gzip import open as gzip_open
from shutil import copy2
from shutil import rmtree
from shutil import copytree
from typing import Any
from typing import Self
from typing import TypeGuard
from typing import final
from typing import get_args
from typing import override
from logging import getLogger
from pathlib import Path
from dataclasses import dataclass
from waydroid_injector.type_defines import ContentType
from waydroid_injector.type_defines import CompressType
from waydroid_injector.deserializable import Deserializable


@final
@dataclass
class Content(Deserializable):
    """Class to describe how to create/remove a content.

    Attributes:
        path(Path): Where to create the content.

        type_(ContentType): What is the content.

        mode_override(int | None): Override default mode value.
        Defaults to None.

        source(Path | None): Where to get the content.
        Defaults to None.

        content(str | None): Write the string as content.
        Defaults to None.

        compress(CompressType | None): How to compress the content.
        Defaults to None.
    """

    path: Path
    type_: ContentType
    mode_override: int | None = None
    source: Path | None = None
    content: str | None = None
    compress: CompressType | None = None

    @property
    def mode(self) -> int:
        """Permission mode of this content.

        If mode_override is None, we will use default value instead.
        Default value depends on type_:
            0o755 if directory,
            0o644 if file,
            0o777 if link.
        """
        return self.mode_override or self.__default_mode

    @property
    def __default_mode(self) -> int:
        match self.type_:
            case "directory":
                return 0o755
            case "file":
                return 0o644
            case "link":
                return 0o777

    def create(  # noqa: PLR0913
        self,
        srcdir: Path,
        name: str,
        version: str,
        overlay: Path,
        overlay_rw: Path,
        user_data: Path,
    ):
        """Create the content.

        Args:
            srcdir(Path): Where the source contents are storaged.
            name(str): The name value in manifest.
            version(str): The version value in manifest.
            overlay(Path): The overlay folder in waydroid's data.
            overlay_rw(Path): The overlay_rw folder in waydroid's data.
            user_data(Path): The waydroid.host_data_path value in waydroid.prop file.
        """
        logger = getLogger(__name__)
        path = Path(
            str(self.path).format(
                overlay=overlay,
                overlay_rw=overlay_rw,
                user_data=user_data,
            ),
        )
        source = (
            Path(
                str(self.source).format(
                    srcdir=srcdir,
                    name=name,
                    version=version,
                    overlay=overlay,
                    overlay_rw=overlay_rw,
                    user_data=user_data,
                ),
            )
            if self.source is not None
            else None
        )

        path.parent.mkdir(exist_ok=True, parents=True)
        if self.content is not None:
            match self.compress:
                case "gz":
                    logger.debug("Compressing content with gzip...")
                    with gzip_open(path, "wt") as writer:
                        _ = writer.write(self.content)
                case None:
                    logger.debug("Writing content without compression...")
                    _ = path.write_text(self.content)
        elif source is not None:
            match self.type_:
                case "directory":
                    logger.debug("Copying directory from %s to %s...", source, path)
                    copytree(source, path, dirs_exist_ok=True)
                case "file":
                    logger.debug("Copying file from %s to %s...", source, path)
                    copy2(source, path)
                case "link":
                    logger.debug(
                        "Creating symbolic link at %s points to %s",
                        path,
                        source,
                    )
                    path.symlink_to(source)
        elif self.type_ == "directory":
            logger.debug("Creating empty directory at %s", path)
            path.mkdir(parents=True, exist_ok=True)
        elif self.type_ == "file":
            logger.debug("Creating empty file at %s", path)
            path.touch(exist_ok=True)

        if (
            path.exists(follow_symlinks=False)
            and path.lstat().st_mode & 0o777 != self.mode
        ):
            logger.debug("Changing mode to %o", self.mode)
            path.lchmod(self.mode)

    def remove(
        self,
        overlay: Path,
        overlay_rw: Path,
        user_data: Path,
    ):
        """Remove the content.

        Args:
            overlay(Path): The overlay folder in waydroid's data.
            overlay_rw(Path): The overlay_rw folder in waydroid's data.
            user_data(Path): The waydroid.host_data_path value in waydroid.prop file.
        """
        logger = getLogger(__name__)
        path = Path(
            str(self.path).format(
                overlay=overlay,
                overlay_rw=overlay_rw,
                user_data=user_data,
            ),
        )
        if path.exists():
            match self.type_:
                case "directory":
                    logger.debug("Removing directory %s...", path)
                    rmtree(path)
                case "file" | "link":
                    logger.debug("Removing file/link %s...", path)
                    path.unlink()
        else:
            logger.warning("%s is not found.", path)

    @property
    @override
    def valid(self) -> bool:
        return (
            self.content is not None
            or self.source is not None
            or self.type_ == "directory"
        )

    @classmethod
    @override
    def load(cls, data: dict[str, Any]) -> Self:
        path_str: str | None = data.get("path")
        if path_str is None:
            raise ValueError("Content.path should not be None.")
        path = Path(path_str)
        type_str = data.get("type")

        def ensure_type(i: Any) -> TypeGuard[ContentType]:  # noqa: ANN401 # pyright: ignore[reportAny]
            return i in get_args(ContentType.__value__)  # pyright: ignore[reportAny]

        if not ensure_type(type_str):
            raise ValueError("Content.type is not valid.")
        type_ = type_str
        mode_override: int | None = data.get("mode")
        source_str: str | None = data.get("source")
        source = Path(source_str) if source_str is not None else None
        content: str | None = data.get("content")

        def ensure_compress(i: Any) -> TypeGuard[CompressType | None]:  # noqa: ANN401 # pyright: ignore[reportAny]
            return i is None or i in get_args(CompressType.__value__)  # pyright: ignore[reportAny]

        compress_str = data.get("compress")
        if not ensure_compress(compress_str):
            raise ValueError("Content.compress is not valid.")
        compress = compress_str
        return cls(path, type_, mode_override, source, content, compress)
