# OrgChart Populator

## Configuration

Visit https://airtable.com/create/tokens and create a token with `data.records:read` and `data.records:write`. A

Create a file called `private.json` as a sibling to `main.py` and populate it 
as follows:

```json
{
  "PAT": "",
  "BASE_ID": "",
  "ALL_STAFF_TABLE_ID": "",
}
```

## Installation
 1. Install [pipenv](https://pipenv.pypa.io/en/latest/)
 1. Clone and then `pipenv install`.

Alternatively, install the dependencies listed in [Pipfile](Pipfile) into your 
environment.

## Running

Configure as explained above, then look at the end of `main.py`.
