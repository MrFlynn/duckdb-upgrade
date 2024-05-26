from enum import Enum, auto
from packaging.version import Version
from pathlib import Path
from typing import List, Union

from .platform import get_platform_details

HEADER_OFFSET = 8
HEADER_MAGIC_SIZE = 4
HEADER_MAGIC_STRING = b"DUCK"
HEADER_VERSION_SIZE = 1


def get_duckdb_version(database_file: Path) -> int:
    with database_file.open("rb") as db_file:
        db_file.seek(HEADER_OFFSET)

        if db_file.read(HEADER_MAGIC_SIZE) != HEADER_MAGIC_STRING:
            raise IOError(f"{database_file} is not a valid DuckDB file")

        return int.from_bytes(db_file.read(HEADER_VERSION_SIZE), byteorder="big")


class VersionError(Exception):
    def __init__(self, storage_version: Union[int, Version]) -> None:
        super().__init__(storage_version)

        self.storage_version = storage_version

    def __str__(self) -> str:
        return f"{self.storage_version} is an invalid storage version"


class VersionUpgradeCheckResult(Enum):
    NoAction = auto()
    Upgrade = auto()
    Invalid = auto()


class VersionLookup:
    DUCKDB_CLI_DOWNLOAD_URL = "https://github.com/duckdb/duckdb/releases/download/v{version}/duckdb_cli-{platform}-{arch}.zip"

    # Based on the following struct:
    # https://github.com/duckdb/duckdb/blob/dae3b286b04cb2e89cf624e6104c94afaf5b7468/src/storage/storage_info.cpp#L12
    VERSION_TABLE = {
        64: [
            Version("0.9.0"),
            Version("0.9.1"),
            Version("0.9.2"),
            Version("v0.10.0"),
            Version("v0.10.1"),
            Version("v0.10.2"),
        ],
        51: [Version("0.8.0"), Version("0.8.1")],
        42: [Version("0.7.0"), Version("0.7.1")],
        39: [Version("0.6.0"), Version("0.6.1")],
        38: [Version("0.5.0"), Version("0.5.1")],
        33: [Version("0.3.3"), Version("0.3.4"), Version("0.4.0")],
        31: [Version("0.3.2")],
        27: [Version("0.3.1")],
        25: [Version("0.3.0")],
        21: [Version("0.2.9")],
        18: [Version("0.2.8")],
        17: [Version("0.2.7")],
        15: [Version("0.2.6")],
        13: [Version("0.2.5")],
        11: [Version("0.2.4")],
        6: [Version("0.2.3")],
        4: [Version("0.2.2")],
        1: [Version("0.2.1")],
    }

    def __init__(self) -> None:
        return

    def latest(self, storage_version: int = 0) -> Version:
        if storage_version <= 0:
            storage_version = max(self.VERSION_TABLE.keys())

        try:
            return max(self.VERSION_TABLE[storage_version])
        except KeyError:
            raise VersionError(storage_version)

    def all_versions_for_storage_number(self, storage_version: int) -> List[Version]:
        try:
            return self.VERSION_TABLE[storage_version]
        except:
            raise VersionError(storage_version)

    def _reverse_version_lookup(self, version: Version) -> int:
        reversed_index = {v: k for k, l in self.VERSION_TABLE.items() for v in l}

        try:
            return reversed_index[version]
        except KeyError:
            raise VersionError(version)

    def can_upgrade_to(
        self, current: int, target: Union[int, Version]
    ) -> VersionUpgradeCheckResult:
        target_storage_version = 0

        if isinstance(target, Version):
            target_storage_version = self._reverse_version_lookup(target)
        else:
            target_storage_version = target

        if target_storage_version < current:
            return VersionUpgradeCheckResult.Invalid
        elif target_storage_version == current:
            return VersionUpgradeCheckResult.NoAction
        else:
            return VersionUpgradeCheckResult.Upgrade

    def get_download_url(self, version: Union[int, Version]) -> str:
        semver = Version("0.0.0")

        if isinstance(version, int):
            semver = self.latest(version)
        else:
            _ = self._reverse_version_lookup(
                version
            )  # Guard to check that this version is real.
            semver = version

        platform_details = get_platform_details()
        return self.DUCKDB_CLI_DOWNLOAD_URL.format(
            version=semver,
            platform=platform_details.Platform,
            arch=platform_details.get_arch(),
        )
