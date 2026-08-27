# PostgreSQL setup

The local development database is PostgreSQL + PostGIS.

Expected database:

```text
testhp_digital_twin
```

## Windows PowerShell

From a new PowerShell session, set the connection string using the password chosen for the local `postgres` role:

```powershell
$env:TESTHP_DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/testhp_digital_twin"
```

Install the Python driver from the repository root:

```powershell
python -m pip install -r requirements.txt
```

Apply the schema with `psql`:

```powershell
psql -U postgres -h localhost -d testhp_digital_twin -f database/schema.sql
```

Verify the database from PowerShell:

```powershell
psql -U postgres -h localhost -d testhp_digital_twin -c "SELECT PostGIS_Version();"
```

Then start the API:

```powershell
uvicorn backend.app:app --reload
```

And open:

```text
http://127.0.0.1:8000/api/system/database
```

A healthy response should contain `connected: true` and `schema_tables: 6`.

## Design rule

PostgreSQL stores structured biological-twin metadata, provenance, observations and stage records. Large binary files such as photographs, WSI, MRI volumes and sequencing files should remain in controlled file/object storage; the database stores identifiers, metadata, lineage, quality, confidence and spatial references.

The schema uses PostGIS for spatial observations so the canonical `HAND_COORDINATE_SYSTEM` can later be represented by explicit geometry and transforms.
