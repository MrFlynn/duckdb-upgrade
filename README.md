# duckdb-upgrade

[![Tests](https://github.com/MrFlynn/duckdb-upgrade/actions/workflows/test.yaml/badge.svg)](https://github.com/MrFlynn/duckdb-upgrade/actions/workflows/test.yaml)

A tool to easily upgrade duckdb databases from one version to another. It
automates the process of exporting the contents of a DuckDB database and
then importing them into a newer version of a DuckDB database.

> [!IMPORTANT]
> This process isn't guaranteed to be compatible with every combination
> of DuckDB. The tool is limited to forward upgrades only, but things
> may still break during that upgrade. By default this tool keeps a
> backup of the old version of the database, but it is still important to be
> mindful of any process that may cause data corruption. Any data loss or
> corruption is on you, so exercise reasonable precautions before use.

# Usage
This tool is available both through pip and Docker. Use one of the following
commands to run it, or your preferred method to run Python packages or Docker
images. These examples cover upgrading some DuckDB in the current directory
to the latest version of the database.

## via Pipx
```bash
$ pipx run duckdb-upgrade example.duckdb
```

## via Docker
```bash
$ docker run -v $(pwd):/data ghcr.io/mrflynn/duckdb-upgrade:latest /data/example.duckdb
```

## Advanced Usage
You can also specify the target version you with to upgrade to using the `-t` flag.
For example, if you wish to upgrade some database to version 0.10.0, run the command
as follows:

```bash
$ duckdb-upgrade -t '0.10.0' example.duckdb
```

> [!CAUTION]
> You can also run the tool with the `--no-backup` flag which won't create a backup
> of the original database before upgrading it. This is potentially dangerous, so
> please use with caution. Again, any data loss resulting from this is on you.
