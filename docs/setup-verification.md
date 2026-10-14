# RoomIQ — Phase 1: Repository and Dataset Verification Report

**Date & Time**: 2026-10-13 16:32 IST  
**Project**: RoomIQ (Occupancy Detection & Monitoring)  
**Project Root**: `C:\Users\priya\Desktop\capstone`  
**Status**: Verification Complete (Small non-destructive setup corrections applied)

---

## 1. Project Root & Repository Structure

### 1.1 Directory Tree (High-Level)
```text
C:\Users\priya\Desktop\capstone
├── .gitignore                      # [Created during Phase 1] Root ignore rules
├── docs/
│   └── setup-verification.md       # [This document] Verification report
├── frontend/                       # Next.js 16.4 frontend application
│   ├── .git/                       # Standalone Git repository created by create-next-app
│   ├── .gitignore                  # Frontend ignore file
│   ├── eslint.config.mjs           # ESLint 9 configuration
│   ├── next.config.ts              # Next.js configuration
│   ├── package.json                # Frontend package manifest
│   ├── package-lock.json           # Locked npm dependencies
│   ├── tsconfig.json               # TypeScript configuration
│   ├── node_modules/               # Installed npm packages (verified present)
│   ├── public/                     # Static assets (file.svg, globe.svg, next.svg, etc.)
│   └── src/
│       └── app/                    # Next.js App Router (layout.tsx, page.tsx, globals.css)
└── ml/                             # Machine Learning & Backend
    ├── .venv/                      # Python 3.12.0 virtual environment
    ├── requirements.txt            # Python dependencies (re-encoded to UTF-8)
    └── data/
        └── raw/                    # UCI Occupancy Detection raw data files
            ├── datatraining.txt
            ├── datatest.txt
            └── datatest2.txt
```

---

## 2. Dataset Verification

All three required dataset files were located in `ml/data/raw/`. Their file sizes and exact line counts were verified:

| File Name | Exact Path | Size (Bytes) | Size (KB) | Total Lines | Data Rows |
|---|---|---|---|---|---|
| `datatraining.txt` | `C:\Users\priya\Desktop\capstone\ml\data\raw\datatraining.txt` | 596,674 | 582.7 KB | 8,144 | 8,143 |
| `datatest.txt` | `C:\Users\priya\Desktop\capstone\ml\data\raw\datatest.txt` | 200,766 | 196.1 KB | 2,666 | 2,665 |
| `datatest2.txt` | `C:\Users\priya\Desktop\capstone\ml\data\raw\datatest2.txt` | 699,664 | 683.3 KB | 9,753 | 9,752 |
| **Total** | — | **1,497,104** | **1,462.1 KB** | **20,563** | **20,560** |

### 2.1 Schema & Formatting Observations
1. **Header vs Data Column Count Mismatch**:
   - Header line: `"date","Temperature","Humidity","Light","CO2","HumidityRatio","Occupancy"` (7 columns).
   - Data lines contain **8** comma-separated items because each row begins with a numeric row index (e.g. `"1"` or `"140"`), followed by timestamp, 5 environmental sensor readings, and binary `Occupancy` label (0 or 1).
   - *Parsing recommendation*: In pandas, load using `pd.read_csv(..., index_col=0)` so the first column is treated as index and column names map correctly to features.
2. **Timestamp Quoting Variations**:
   - `datatraining.txt` and `datatest.txt` have quoted timestamps (e.g. `"2015-02-04 17:51:00"`).
   - `datatest2.txt` has unquoted timestamps (e.g. `2015-02-11 14:48:00`).

### 2.2 Attribution & License Check
- **Official Source**: UCI Machine Learning Repository — Occupancy Detection Data Set.
- **Creators / Authors**: Luis M. Candanedo and V. Vélez (2016), University of Mons.
- **Paper Citation**: Candanedo, L.M. & Vélez, V. (2016). *Accurate occupancy detection of an office room from light, temperature, humidity and CO2 measurements using statistical learning models*. Energy and Buildings, 112, 28–39. DOI: [10.1016/j.enbuild.2016.01.001](https://doi.org/10.1016/j.enbuild.2016.01.001).
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Current Repository Status**: **Not documented**. Neither a `LICENSE` file nor attribution notes existed in the workspace prior to this audit.

---

## 3. Frontend Verification

- **Path**: `C:\Users\priya\Desktop\capstone\frontend`
- **Manifest (`package.json`)**: Valid JSON.
- **Available npm Scripts**:
  - `npm run dev`: Runs Next.js development server (`next dev`).
  - `npm run build`: Compiles application for production (`next build`).
  - `npm run start`: Launches production server (`next start`).
  - `npm run lint`: Runs ESLint 9 analysis (`eslint`).
- **Core Dependencies**: Next.js `16.4.0`, React `19.3.0`, React DOM `19.3.0`.
- **Dev Dependencies**: `@tailwindcss/turbopack ^4`, `tailwindcss ^4`, `typescript ^5`, `eslint ^9`, `eslint-config-next 16.4.0`.
- **Package Installation**: `node_modules` directory exists and `package-lock.json` is present.

---

## 4. Python Environment & Dependency Verification

- **Environment Path**: `C:\Users\priya\Desktop\capstone\ml\.venv`
- **Python Version**: `3.12.0` (64-bit, Windows)
- **Requirements File**: `ml/requirements.txt` (45 pinned dependencies).

### 4.1 Dependency Import Verification (Executed in `ml/.venv`)
All required packages were tested by executing an import probe in `ml\.venv\Scripts\python.exe`:

| Package | Status | Detected Version | Purpose |
|---|---|---|---|
| `pandas` | Available | `3.0.6` | Data loading and tabular manipulation |
| `numpy` | Available | `2.5.4` | Numerical operations & array processing |
| `scikit-learn` (`sklearn`) | Available | `1.9.1` | Model training, pipelines, metrics |
| `joblib` | Available | `1.6.0` | Model serialization and persistence |
| `fastapi` | Available | `0.143.0` | REST API development |
| `uvicorn` | Available | `0.54.0` | ASGI web server |
| `pytest` | Available | `9.1.1` | Test framework |

---

## 5. Security & Secrets Check

- **Local `.env` files**: Checked all subfolders. No `.env`, `.env.local`, or secret config files are present.
- **Exposure Risk**: Zero credentials or sensitive environment tokens detected.

---

## 6. Git & Ignore Rules Verification

### 6.1 Previous State
- The root project directory `C:\Users\priya\Desktop\capstone` had **no `.gitignore`**.
- Only `frontend/.gitignore` existed (ignoring `frontend/node_modules`, `frontend/.next`, etc.).
- `ml/.venv/`, python bytecode caches (`__pycache__`), pytest caches (`.pytest_cache`), and model checkpoints were unprotected at the root level.

### 6.2 Correction Applied
A root-level `.gitignore` was created at `C:\Users\priya\Desktop\capstone\.gitignore` protecting:
- Python virtual environments (`.venv/`, `ml/.venv/`)
- Python caches (`__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`)
- Node modules and Next.js artifacts (`node_modules/`, `frontend/node_modules/`, `frontend/.next/`, `build/`, `out/`)
- Local environment files (`.env`, `.env.*`, preserving `!.env.example`)
- ML model artifacts (`ml/models/*.pkl`, `ml/models/*.joblib`, `*.onnx`)
- OS and IDE metadata (`.DS_Store`, `Thumbs.db`, `.vscode/`, `.idea/`)

---

## 7. Corrections & Actions Completed in Phase 1

1. **Re-encoded `ml/requirements.txt` from UTF-16LE to UTF-8**:
   - The file was initially generated with UTF-16LE (common when using PowerShell redirection), preventing cross-platform CLI tools and IDEs from parsing it properly. Re-encoded cleanly to UTF-8 without changing package versions.
2. **Created Root `.gitignore`**:
   - Added standard repository-wide ignore definitions to safeguard virtual environments, dependencies, and caches.
3. **Created `docs/` and `docs/setup-verification.md`**:
   - Documented the verified status of the repository, dataset, and environments.

---

## 8. Remaining Structural Inconsistencies & Issues

1. **Root Git Repository Not Initialized**:
   - The workspace root `capstone/` is not a git repository.
   - However, `frontend/.git/` exists because `create-next-app` automatically initialized an independent Git repo inside `frontend/`.
   - *Recommendation*: If you want a unified mono-repository tracking both `frontend` and `ml`, remove `frontend/.git` and initialize `git init` at the root `capstone/`.
2. **Missing Dataset Documentation**:
   - Neither the UCI citation nor the CC BY 4.0 license is currently documented inside `ml/data/` or `docs/`.
3. **Missing Backend Directory Structure**:
   - While `ml/data/raw/` and `ml/.venv/` are present, backend code structures (`ml/src/`, `ml/models/`, `ml/tests/`) have not yet been scaffolded.

---

## 9. Next Steps

Before proceeding to Phase 2 (Data Cleaning & Exploration):
- Confirm whether to unite the Git structure under a single root repository.
- Scaffold dataset documentation in `ml/data/README.md`.
