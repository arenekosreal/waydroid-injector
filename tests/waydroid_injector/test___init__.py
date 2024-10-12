"""Test src/waydroid_injector/__init__.py."""

# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnusedParameter=false
# pyright: reportAny=false

import pytest
from logging import INFO
from logging import DEBUG
from logging import getLogger
from pathlib import Path
from waydroid_injector import setup_logger
from waydroid_injector import is_entrypoint


def _mock_function_with_type_int_and_bool(_: int, __: bool):
    return


def _mock_function_with_type_bool_and_path(_: bool, __: Path):
    return


def _mock_function_with_type_bool_and_path_with_return_int(_: bool, __: Path) -> int:
    return 1


def _mock_function_with_type_bool_and_path_with_return_none(_: bool, __: Path) -> None:
    return None


class _MockInstanceFunction:
    """Test is_entrypoint when instance is True."""

    def mock_function_with_no_parameter(self):
        return

    def mock_function_with_1_parameter(self, _: object):
        return

    def mock_function_with_2_parameters(self, _: object, __: object):
        return

    def mock_function_with_type_int_and_bool(self, _: int, __: bool):
        return

    def mock_function_with_type_bool_and_path(self, _: bool, __: Path):
        return

    def mock_function_with_type_bool_and_path_with_return_int(
        self,
        _: bool,
        __: Path,
    ) -> int:
        return 1

    def mock_function_with_type_bool_and_path_with_return_none(
        self,
        _: bool,
        __: Path,
    ) -> None:
        return None


_mock = _MockInstanceFunction()


@pytest.mark.parametrize(
    ("o", "result"),
    [
        (None, False),
        (1, False),
        (True, False),
        (1.0, False),
        (lambda: None, False),
        (lambda _: None, False),
        (lambda _, __: None, False),
        (_mock_function_with_type_int_and_bool, False),
        (_mock_function_with_type_bool_and_path_with_return_int, False),
        (_mock_function_with_type_bool_and_path, True),
        (_mock_function_with_type_bool_and_path_with_return_none, True),
        (_mock.mock_function_with_no_parameter, False),
        (_mock.mock_function_with_1_parameter, False),
        (_mock.mock_function_with_2_parameters, False),
        (_mock.mock_function_with_type_int_and_bool, False),
        (_mock.mock_function_with_type_bool_and_path_with_return_int, False),
        (_mock.mock_function_with_type_bool_and_path, True),
        (_mock.mock_function_with_type_bool_and_path_with_return_none, True),
    ],
)
def test_is_entrypoint(o: object, result: bool):
    """Test is_entrypoint function with values given."""
    assert is_entrypoint(o) == result


@pytest.mark.parametrize(
    ("debug", "level"),
    [
        (True, DEBUG),
        (False, INFO),
    ],
)
def test_setup_logger(debug: bool, level: int):
    """Test setup_logger function."""
    logger = getLogger("waydroid_injector.test")
    setup_logger(logger, debug)
    assert logger.level == level
