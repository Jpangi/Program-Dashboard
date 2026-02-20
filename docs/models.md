# EVMS Django Models Documentation

This document explains the purpose of each model in the EVMS system.

The system follows a hierarchical structure:

```
Program
 ├── ControlAccount
 │    ├── WorkPackage
 │    │    └── EVMData
 │    └── EVMSnapshot
 └── CSVupload
```

---

# Program Model

The `Program` model represents the top-level.

This is the root for all EVMS data.

It stores:

- Program identity
- Period of performance
- Aggregated performance metrics (CPI, SPI, etc.)

This is the primary object displayed on dashboards.

## Relationships

A Program contains:

- Many ControlAccounts
- Many EVMSnapshots
- Many CSVuploads

## Example

```
program.control_accounts.all()
program.snapshots.all()
program.latest_bcwp
```

---

# ControlAccount Model

## Relationships

Each ControlAccount belongs to:

- One Program

Each ControlAccount contains:

- Many WorkPackages
- Many EVMData rows
- Many EVMSnapshots

## Example

```
ca.program
ca.work_packages.all()
ca.evm_data.all()
```

---

# WorkPackage Model

This is the lowest level of planned work.

Work Packages allow detailed tracking within Control Accounts.

## Relationships

Each WorkPackage belongs to:

- One ControlAccount

Each WorkPackage contains:

- Many EVMData rows

## Example

```
wp.control_account
wp.evm_data.all()
```

---

# EVMData Model

Stores raw EVMS data imported from CSV files.

Each row represents:

- One Control Account and Work Package
- One reporting period
- One EVMS metric
- One value

Examples of metrics:

- BCWS (Planned Value)
- BCWP (Earned Value)
- ACWP (Actual Cost)
- EAC (Estimate at Completion)

This table powers all calculations.

This will be the largest table in the database.

## Relationships

Each EVMData row belongs to:

- One ControlAccount
- One WorkPackage

## Example

```
ca.evm_data.all()

EVMData.objects.filter(
    cobra_set="BCWP"
)
```

---

# EVMSnapshot Model

Stores pre-calculated monthly performance metrics.

It improves performance by avoiding recalculating metrics every time.

Used for:

- Dashboard performance
- Trend charts
- Historical reporting

Snapshots are generated automatically after CSV imports.

## Stored Metrics

- BCWS total
- BCWP total
- ACWP total
- EAC total
- CPI
- SPI
- CV
- SV

## Relationships

Each snapshot belongs to:

- One Program
- One ControlAccount

## Example

```
program.snapshots.all()

ca.snapshots.order_by("snapshot_date")
```

---

# CSVupload Model

Tracks uploaded CSV files.

Provides:

- Upload history
- Processing status
- Audit trail
- Error tracking

## Status Options

- pending
- processing
- completed
- failed

## Relationships

Each CSVupload belongs to:

- One Program
- One User

## Example

```
program.csv_upload.all()
```

---

# Data Flow Overview

```
CSVupload
   ↓
EVMData (raw)
   ↓
EVMSnapshot (aggregated)
   ↓
Program calculations
   ↓
Dashboard
```

---

# Table Roles Summary

| Model | Role |
|---|---|
| Program | Top-level container |
| ControlAccount | Management unit |
| WorkPackage | Task unit |
| EVMData | Raw fact table |
| EVMSnapshot | Aggregated performance |
| CSVupload | File tracking |

---


