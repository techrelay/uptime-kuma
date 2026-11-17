#!/usr/bin/env python3
"""Import an existing private Uptime Kuma SQLite backup without overwriting data."""
import argparse
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    target = args.data_dir.resolve()
    database = target / "kuma.db"
    if database.exists():
        parser.error(f"Refusing to overwrite existing database: {database}")
    if (target / "db-config.json").exists():
        parser.error(f"Existing DB configuration at {target}; refusing ambiguous import")
    with zipfile.ZipFile(args.archive) as archive:
        if archive.namelist().count("kuma.db") != 1:
            parser.error("ZIP must contain exactly one root-level kuma.db")
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".kuma-import-", suffix=".db", dir=target, delete=False) as tmp:
            temp_path = Path(tmp.name)
            with archive.open("kuma.db") as source:
                shutil.copyfileobj(source, tmp)
    try:
        con = sqlite3.connect(f"file:{temp_path}?mode=ro", uri=True)
        try:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                parser.error("SQLite integrity check failed")
            tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"monitor", "heartbeat", "setting", "user"}.issubset(tables):
                parser.error("Unrecognized Uptime Kuma database schema")
            monitor_count = con.execute("SELECT COUNT(*) FROM monitor").fetchone()[0]
            heartbeat_count = con.execute("SELECT COUNT(*) FROM heartbeat").fetchone()[0]
        finally:
            con.close()
        if database.exists():
            parser.error(f"Database appeared during import: {database}")
        os.chmod(temp_path, 0o600)
        temp_path.replace(database)
        print(f"Imported {monitor_count} monitors and {heartbeat_count} heartbeats into {database}")
        print("Keep the original ZIP as an offline backup; v3 startup may migrate its schema.")
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    try:
        main()
    except (OSError, sqlite3.DatabaseError, zipfile.BadZipFile) as exc:
        sys.exit(f"Import failed: {exc}")
