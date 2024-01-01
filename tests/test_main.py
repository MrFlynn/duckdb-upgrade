import pytest

from duckdb_upgrade.__main__ import get_executable, DuckDBOperation
from packaging.version import Version
from typing import NamedTuple


def test_get_executable() -> None:
    class Test(NamedTuple):
        URL: str
        ShouldAssert: bool

    tests = [
        Test(
            URL="https://github.com/duckdb/duckdb/releases/download/v0.9.2/duckdb_cli-linux-amd64.zip",
            ShouldAssert=False,
        ),
        Test(
            URL="https://github.com/duckdb/duckdb/releases/download/v100/duckdb_cli-linux-amd64.zip",
            ShouldAssert=True,
        ),
    ]

    for test in tests:
        if not test.ShouldAssert:
            executable = get_executable(test.URL, Version("0.0.0"))

            try:
                assert executable.exists()
                assert executable.is_file()
                assert (executable.stat().st_mode & 0o777) == 0o744
                assert executable.parent.name.startswith("duckdb_bin_0.0.0")
            finally:
                executable.unlink()
        else:
            with pytest.raises(RuntimeError):
                get_executable(test.URL, Version("0.0.0"))


def test_duckdb_operation_str() -> None:
    class Test(NamedTuple):
        Operation: DuckDBOperation
        Result: str

    tests = [
        Test(Operation=DuckDBOperation.Export, Result="EXPORT"),
        Test(Operation=DuckDBOperation.Import, Result="IMPORT"),
    ]

    for test in tests:
        assert str(test.Operation) == test.Result
