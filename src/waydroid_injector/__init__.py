"""Inject custom content described in a manifest into waydroid's data."""

# pyright: reportAny=false

from types import UnionType
from typing import Any
from typing import TypeGuard
from typing import get_args
from typing import get_origin
from inspect import signature
from logging import INFO
from logging import DEBUG
from logging import Logger
from logging import Formatter
from logging import StreamHandler
from logging import getLogger
from pathlib import Path
from tomllib import loads
from argparse import Namespace
from argparse import ArgumentParser
from collections.abc import Sequence
from waydroid_injector.manifest import Manifest
from waydroid_injector.type_defines import EntrypointFunctionType


__version__ = "0.1.0"


def _type_accepted(i: Any, *ts: type | None) -> bool:  # noqa: ANN401
    if i in ts:
        return True
    if get_origin(i) is UnionType:
        return any(t in get_args(i) for t in ts)
    return False


def is_entrypoint(o: object) -> TypeGuard[EntrypointFunctionType]:
    """Check if object is valid entrypoint function."""
    if not callable(o):
        return False
    required_parameters_count = 2
    sig = signature(o)
    parameters = list(sig.parameters.values())
    if len(parameters) < required_parameters_count:
        return False
    parameters_kind_correct = all(
        parameter.kind == parameter.POSITIONAL_OR_KEYWORD
        for parameter in parameters[:required_parameters_count]
    )
    parameters_type_correct = _type_accepted(
        parameters[0].annotation,
        bool,
    ) and _type_accepted(parameters[1].annotation, Path, None)
    parameters_correct = parameters_kind_correct and parameters_type_correct
    returns_correct = (
        sig.return_annotation is None or sig.return_annotation is sig.empty
    )
    return parameters_correct and returns_correct


def parse_args(args: Sequence[str] | None = None) -> Namespace:
    """Parse arguments."""
    root = ArgumentParser(description=__doc__)
    _ = root.add_argument("-v", "--version", action="version", version=__version__)
    _ = root.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="install contents into ./slash directory.",
    )
    _ = root.add_argument(
        "-e",
        "--debug",
        action="store_true",
        help="enable debug mode.",
    )
    _ = root.add_argument("-s", "--destdir", type=Path, help="destination to rootfs.")
    operations = root.add_subparsers(
        title="operations",
        description="available operations:",
        required=True,
        dest="operation",
    )
    install = operations.add_parser(
        "install",
        help="Install the manifest into waydroid's data.",
    )
    _ = install.add_argument("manifest", type=Path, help="the path to the manifest.")
    uninstall = operations.add_parser(
        "uninstall",
        help="Uninstall the manifest from waydroid's data.",
    )
    _ = uninstall.add_argument("manifest", type=Path, help="the path to the manifest.")

    return root.parse_args(args)


def setup_logger(logger: Logger, debug: bool):
    """Setup the logger."""
    logger.setLevel(DEBUG if debug else INFO)
    logger.addHandler(StreamHandler())
    for handler in logger.handlers:
        handler.setFormatter(
            Formatter(
                "%(asctime)s-%(levelname)s-%(message)s",
                "%Y-%m-%d %H:%M:%S",
            ),
        )
        handler.setLevel(logger.level)


def main():
    """Main entrance of waydroid_injector."""
    args = parse_args()
    setup_logger(getLogger(__name__), args.debug)
    data = loads(args.manifest.read_text())
    manifest = Manifest.load(data)
    if not manifest.valid:
        raise ValueError("Manifest is not valid.")
    func = getattr(manifest, args.operation)
    if not is_entrypoint(func):
        raise ValueError("No such operation {}".format(args.operation))
    func(args.dry_run, Path("slash") if args.dry_run else args.destdir)
