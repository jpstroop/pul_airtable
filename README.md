# PUL Staff Airtable

## Configuration

### Setting Up Test and Production Environments

This tool uses separate **test** and **production** Airtable bases for safety. In particular, the test environment lets you manually test sync workflows without affecting the production base.

### Authentication

Visit https://airtable.com/create/tokens and create a token (or two separate tokens) with `data.records:read` and `data.records:write` permissions.

### Configuration File

Create a file called `private.json` as a sibling to `main.py`:

```json
{
  "test": {
    "PAT": "your_test_airtable_token",
    "BASE_ID": "your_test_base_id",
    "ALL_STAFF_TABLE_ID": "test_all_staff_table_id",
    "REMOVAL_TABLE_ID": "test_removal_table_id"
  },
  "production": {
    "PAT": "your_production_airtable_token",
    "BASE_ID": "your_production_base_id",
    "ALL_STAFF_TABLE_ID": "production_all_staff_table_id",
    "REMOVAL_TABLE_ID": "production_removal_table_id"
  }
}
```

**Note**: You can use the same PAT for both environments if desired, but the base IDs should be different. If you copied the test base from produciton, the table IDs might be the same, but the base ids will be different.

### ⚠️ Security and Privacy

**IMPORTANT**: This application handles sensitive data.

- **NEVER commit `private.json`** - it contains API credentials and is in `.gitignore`
- **NEVER commit CSV files** - they contain personal employee data
- **NEVER commit real employee data** - use mock data in test fixtures
- **Test fixtures should use synthetic data only** - generic names, fake IDs, placeholder information
- Always verify that no sensitive data is staged before committing: `git diff --staged`

## Installation

1. Install [PDM](https://pdm-project.org/)
2. Clone this repository
3. Run `pdm install`

## Running

### Test Environment (Default - Recommended First)

All commands use the **test** Airtable base by default for safety. Try these first:

```bash
# Run consistency checks on TEST base
pdm run pul-staff check

# Sync CSV data to TEST base (interactive prompts)
pdm run pul-staff sync

# Update supervisor hierarchy on TEST base
pdm run pul-staff update-supervisors
```

### Production Environment (Requires Explicit Flag)

Once you're comfortable with the workflow in test, use the `--production` / `-p` flag:

```bash
# Run checks on PRODUCTION
pdm run pul-staff --production check

# Sync to PRODUCTION (prompts for confirmation)
pdm run pul-staff --production sync

# Update supervisors on PRODUCTION
pdm run pul-staff --production update-supervisors
```

### Additional Options

```bash
# Specify custom CSV file path
pdm run pul-staff --csv ./path/to/report.csv sync

# Get help
pdm run pul-staff --help
pdm run pul-staff sync --help
```

## Development

### Running Tests

The test suite uses pytest with comprehensive coverage for all modules:

```bash
# Run all tests and get a coverage report
pdm test

# Run specific test file
pdm run pytest tests/test_sync_validator.py

```

All tests use mock data and fixtures - no real employee data is required or used in tests.

### Type Checking

The project uses mypy with strict type checking enabled:

```bash
# Run mypy on entire project
pdm mypy

# Run mypy on specific module
pdm mypy staff_management/

# Run mypy on specific file
pdm mypy main.py
```

All code must pass mypy strict type checking with no errors.
