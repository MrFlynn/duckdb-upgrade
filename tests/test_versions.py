import platform
import pytest
import sys
import tempfile

from packaging.version import Version
from pathlib import Path
from src.duckdb_upgrade import versions
from typing import NamedTuple, Union


def test_get_duckdb_version() -> None:
    class Test(NamedTuple):
        FileContent: bytes
        Result: int
        ShouldAssert: bool

    tests = [
        Test(
            FileContent=b"\x00\x00\x00\x00\x00\x00\x00\x00DUCK\x01",
            Result=1,
            ShouldAssert=False,
        ),
        Test(FileContent=b"", Result=0, ShouldAssert=True),
    ]

    for test in tests:
        file_name = None

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            file_name = Path(tf.name)
            tf.write(test.FileContent)

        if not test.ShouldAssert:
            assert versions.get_duckdb_version(file_name) == test.Result
        else:
            with pytest.raises(IOError):
                versions.get_duckdb_version(file_name)

        file_name.unlink()


def test_version_error_str() -> None:
    assert str(versions.VersionError(10)) == "10 is an invalid storage version"


def test_version_lookup_latest() -> None:
    class Test(NamedTuple):
        StorageVersion: int
        Result: Version
        ShouldAssert: bool

    def get_latest_version() -> Version:
        with Path(__file__).resolve().parent.joinpath("latest.txt").open("r") as f:
            return Version(f.read())

    lookup = versions.VersionLookup()
    tests = [
        Test(StorageVersion=0, Result=get_latest_version(), ShouldAssert=False),
        Test(StorageVersion=10000, Result=Version("0.0.0"), ShouldAssert=True),
    ] + [
        Test(StorageVersion=sv, Result=max(vs), ShouldAssert=False)
        for sv, vs in lookup.version_table.items()
    ]

    for test in tests:
        if not test.ShouldAssert:
            assert lookup.latest(test.StorageVersion) == test.Result
        else:
            with pytest.raises(versions.VersionError):
                lookup.latest(test.StorageVersion)


def test_version_lookup_all_versions_for_storage_number() -> None:
    lookup = versions.VersionLookup()

    for sv, vs in lookup.version_table.items():
        assert lookup.all_versions_for_storage_number(sv) == vs


def test_version_lookup_can_upgrade_to() -> None:
    class Test(NamedTuple):
        Current: int
        Target: Union[int, Version]
        Result: versions.VersionUpgradeCheckResult

    lookup = versions.VersionLookup()
    tests = [
        Test(Current=51, Target=64, Result=versions.VersionUpgradeCheckResult.Upgrade),
        Test(
            Current=51,
            Target=Version("0.9.0"),
            Result=versions.VersionUpgradeCheckResult.Upgrade,
        ),
        Test(Current=64, Target=21, Result=versions.VersionUpgradeCheckResult.Invalid),
        Test(
            Current=64,
            Target=Version("0.2.9"),
            Result=versions.VersionUpgradeCheckResult.Invalid,
        ),
        Test(Current=33, Target=33, Result=versions.VersionUpgradeCheckResult.NoAction),
        Test(
            Current=33,
            Target=Version("0.3.3"),
            Result=versions.VersionUpgradeCheckResult.NoAction,
        ),
    ]

    for test in tests:
        assert lookup.can_upgrade_to(test.Current, test.Target) == test.Result


def test_version_lookup_get_download_url(monkeypatch: pytest.MonkeyPatch) -> None:
    class Test(NamedTuple):
        Version: Union[int, Version]
        Platform: str
        Arch: str
        Result: str
        ShouldAssert: bool

    lookup = versions.VersionLookup()
    tests = [
        Test(
            Version=64,
            Platform="linux",
            Arch="x86_64",
            Result="https://github.com/duckdb/duckdb/releases/download/v1.1.3/duckdb_cli-linux-amd64.zip",
            ShouldAssert=False,
        ),
        Test(
            Version=Version("0.9.2"),
            Platform="linux",
            Arch="arm64",
            Result="https://github.com/duckdb/duckdb/releases/download/v0.9.2/duckdb_cli-linux-aarch64.zip",
            ShouldAssert=False,
        ),
        Test(
            Version=Version("1000.1000.1000"),
            Platform="linux",
            Arch="arm64",
            Result="",
            ShouldAssert=True,
        ),
    ]

    for test in tests:
        monkeypatch.setattr(sys, "platform", test.Platform)
        monkeypatch.setattr(platform, "machine", lambda: test.Arch)

        if not test.ShouldAssert:
            assert lookup.get_download_url(test.Version) == test.Result
        else:
            with pytest.raises(versions.VersionError):
                lookup.get_download_url(test.Version)
