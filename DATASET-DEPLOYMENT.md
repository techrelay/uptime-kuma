# Deploy Tech Relay Uptime Kuma using an existing private database

**Never commit a live database or backup to this public repository.** It contains passwords, user credentials and monitor configuration.

## Import

Stop your existing Uptime Kuma instance first and preserve the original backup offline. Place the private `kuma.zip` outside the repository and run from the repository root:

```bash
python3 import-kuma.py /secure/location/kuma.zip --data-dir ./data
```

The importer checks SQLite integrity and expected Uptime Kuma tables, and refuses to overwrite an existing database. The repository already excludes `/data` via `.gitignore`.

## Run this fork

```bash
docker compose -f compose.dataset.yaml build
docker compose -f compose.dataset.yaml up -d
docker compose -f compose.dataset.yaml logs -f uptime-kuma
```

Open port 3001 and sign in with your existing account. Verify monitors, notifications, status pages, and history.

**Compatibility warning:** This repository is currently Uptime Kuma 3.0.0-beta.1; databases from an older Kuma version may require irreversible schema and authentication migrations. Test with a copy, retain the original ZIP, and never run old and new versions against the same live DB simultaneously. SQLite integrity does not prove application compatibility.

The ZIP contains only `kuma.db`; it does not include separately stored uploads, screenshots or certificates. Copy those from the original data directory if required. The `./data:/app/data` mount persists the database through container recreations.
