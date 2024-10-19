"""Generate contents list for manifest based on filesystem structure.

Useful if you want to install huge number of files into waydroid's data.

Usage:
    gen-contents-from-filesystem.py \
        --prefix="{overlay}/system" \
        --srcprefix="{srcdir}" \
        --manifest=/path/to/manifest.toml \
        --srcdir=/path/to/srcdir

Remarks:
    This script use inline script metadata (PEP723) to define dependencies.
    Use any package manager supports PEP723 to run this script
can make your life easier.
"""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tomlkit>=0.13.2"
# ]
# ///

# pyright: reportAny=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false

from logging import StreamHandler
from logging import getLogger
from pathlib import Path
from tomlkit import aot
from tomlkit import dumps
from tomlkit import parse
from tomlkit import table
from tomlkit import value
from tomlkit import document
from argparse import Namespace
from argparse import ArgumentParser


__version__ = "0.1.0"


def _parse_arg(args: list[str] | None = None) -> Namespace:
    root = ArgumentParser()
    _ = root.add_argument("-v", "--version", action="version", version=__version__)
    _ = root.add_argument(
        "-p",
        "--prefix",
        type=str,
        default="{overlay}",
        help="The prefix to the path value..",
    )
    _ = root.add_argument(
        "-r",
        "--srcprefix",
        type=str,
        default="{srcdir}",
        help="The prefix to the source value.",
    )
    _ = root.add_argument(
        "-m",
        "--manifest",
        type=Path,
        required=True,
        help="Where is manifest to be stored/updated.",
    )
    _ = root.add_argument(
        "-s",
        "--srcdir",
        type=Path,
        required=True,
        help="Where is the root directory of contents to be added.",
    )

    return root.parse_args(args)


def _main():
    logger = getLogger(__name__)
    logger.addHandler(StreamHandler())
    logger.setLevel("DEBUG")
    for handler in logger.handlers:
        handler.setLevel(logger.level)
    args = _parse_arg()
    manifest: Path = args.manifest
    srcdir: Path = args.srcdir
    prefix: str = args.prefix
    srcprefix: str = args.srcprefix

    logger.debug(
        "Processing with manifest=%s, srcdir=%s, prefix=%s, srcprefix=%s",
        manifest,
        srcdir,
        prefix,
        srcprefix,
    )

    data = parse(manifest.read_text()) if manifest.exists() else document()

    contents = aot()
    for r, ds, fs in srcdir.walk():
        for d in ds:
            default_mode = 0o755
            logger.info("Processing directory %s...", r / d)
            relative_path = (r / d).relative_to(srcdir)
            content = table(True)
            content.update(
                {
                    "path": str(prefix / relative_path),
                    "type": "directory",
                },
            )

            mode = (r / d).stat().st_mode & 0o777
            if mode != default_mode:
                content["mode"] = value(oct(mode))
            contents.append(content)
        for f in fs:
            if (r / f).is_file():
                default_mode = 0o644
                logger.info("Processing file %s...", r / f)
                relative_path = (r / f).relative_to(srcdir)
                content = table(True)
                content.update(
                    {
                        "path": str(prefix / relative_path),
                        "source": str(srcprefix / relative_path),
                        "type": "file",
                    },
                )
                mode = (r / f).stat().st_mode & 0o777
                if mode != default_mode:
                    content["mode"] = value(oct(mode))
                contents.append(content)

    data.update(contents=contents)
    _ = manifest.write_text(dumps(data))


if __name__ == "__main__":
    _main()
