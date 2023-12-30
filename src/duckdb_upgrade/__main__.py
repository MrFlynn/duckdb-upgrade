import argparse
import shutil
import subprocess
import requests
import tempfile
import zipfile

from enum import StrEnum
from io import BytesIO
from packaging.version import Version
from pathlib import Path

from .versions import VersionLookup, get_duckdb_version

VERSION_LOOKUP = VersionLookup()


def get_executable(url: str, version: Version) -> Path:
    response = requests.get(url)
    if not response.ok:
        raise RuntimeError(
            f"Got invalid status code when requesting file {url}: {response.status_code} {response.reason}"
        )

    storage_dir = Path(tempfile.mkdtemp(prefix=f"duckdb_bin_{version}"))

    duckdb_cli_zip = zipfile.ZipFile(BytesIO(response.content))
    duckdb_cli_zip.extract("duckdb", path=storage_dir)
    duckdb_cli_zip.close()

    binary_path = storage_dir.joinpath("duckdb")
    binary_path.chmod(0o744)

    return binary_path


class DuckDBOperation(StrEnum):
    Export = "EXPORT"
    Import = "IMPORT"


def run_duckdb_migration_command(
    op: DuckDBOperation, binary: Path, db: Path, tempdir: Path
) -> None:
    result = subprocess.run(
        [binary, "-c", f"{str(op)} DATABASE '{tempdir}'", db], capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to {str(op).lower()} database '{db}'."
            + f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )


def run(args: argparse.Namespace) -> None:
    current_storage_version = get_duckdb_version(args.database)

    if not VERSION_LOOKUP.can_upgrade_to(current_storage_version, args.target):
        all_corresponding_versions = VERSION_LOOKUP.all_versions_for_storage_number(
            current_storage_version
        )
        raise RuntimeError(
            f"Cannot upgrade {', '.join([str(v) for v in all_corresponding_versions[:-1]])}, "
            + f"or {all_corresponding_versions[-1]} (storage version: {current_storage_version}) "
            + f"to target version {args.target} "
            + "because the current version of the database is newer than the target version."
        )

    current_version = VERSION_LOOKUP.latest(current_storage_version)
    current_version_bin_path, target_version_bin_path, export_path = None, None, None

    try:
        current_version_bin_path = get_executable(
            VERSION_LOOKUP.get_download_url(current_version), current_version
        )
        target_version_bin_path = get_executable(
            VERSION_LOOKUP.get_download_url(args.target), args.target
        )

        export_path = Path(tempfile.mkdtemp(prefix=f"duckdb_export"))
        run_duckdb_migration_command(
            DuckDBOperation.Export, current_version_bin_path, args.database, export_path
        )

        # Unless explicitly told otherwise, back up the file in the same directory with
        # the '.bak' suffix.
        if not args.no_backup:
            args.database.replace(
                args.database.with_suffix(f"{''.join(args.database.suffixes)}.bak")
            )
        else:
            args.database.unlink()

        run_duckdb_migration_command(
            DuckDBOperation.Import, target_version_bin_path, args.database, export_path
        )
    finally:
        # Always remove temporary directories.
        for dir in [current_version_bin_path, target_version_bin_path, export_path]:
            if dir:
                shutil.rmtree(dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="duckdb_upgrade",
        description="Upgrade DuckDB database file to a specific version",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Version,
        default=VERSION_LOOKUP.latest(),
        required=False,
        help="DuckDB version to upgrade to",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        required=False,
        help="Don't back up the original file",
    )
    parser.add_argument("database", type=Path, help="Path to DuckDB file")

    run(parser.parse_args())


if __name__ == "__main__":
    main()
