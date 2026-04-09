# Operational Scripts

One-shot and maintenance scripts for data backfill and re-processing.

## Usage

All scripts must be run from the `backend/` directory with the virtual
environment activated:

```bash
cd backend
source .venv/bin/activate
python scripts/<script_name>.py
```

## Available Scripts

| Script                  | Purpose                                                                | When to run                                    |
| ----------------------- | ---------------------------------------------------------------------- | ---------------------------------------------- |
| `backfill_comments.py`  | Re-parse PDFs from MinIO and insert missing `comentario_analisis` rows | After fixing the comment parser                |
| `backfill_escuelas.py`  | Derive `escuela` from course-code prefix and clean `\n` from names     | After importing courses without school mapping |
| `backfill_modalidad.py` | Populate `modalidad`, `año`, `periodo_orden` on existing evaluaciones  | After adding modality columns to the schema    |
| `reanalyze_comments.py` | Re-classify all comments with keyword rules, then enrich via Gemini    | After changing classification rules or prompts |

## Safety

- All scripts are **idempotent** — safe to re-run (they skip already-processed rows or overwrite in place).
- They operate inside transactions and commit at the end.
- Run against a **development database first** before production.
