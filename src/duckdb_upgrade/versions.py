import json

from enum import Enum, auto
from packaging.version import Version
from pathlib import Path
from typing import Dict, List, Union

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

    def __init__(self) -> None:
        self.version_table = self._generate_storage_table()
        return

    @staticmethod
    def _generate_storage_table() -> Dict[int, List[Version]]:
        version_map_file = Path(__file__).resolve().parent / "data/version_map.json"

        table = {}
        with version_map_file.open("r") as f:
            for version, storage_number in (
                json.load(f).get("storage", {}).get("values", {}).items()
            ):
                table.setdefault(storage_number, []).append(Version(version))

        return table

    def latest(self, storage_version: int = 0) -> Version:
        if storage_version <= 0:
            storage_version = max(self.version_table.keys())

        try:
            return max(self.version_table[storage_version])
        except KeyError:
            raise VersionError(storage_version)

    def all_versions_for_storage_number(self, storage_version: int) -> List[Version]:
        try:
            return self.version_table[storage_version]
        except:
            raise VersionError(storage_version)

    def _reverse_version_lookup(self, version: Version) -> int:
        reversed_index = {v: k for k, l in self.version_table.items() for v in l}

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
