# OrgChart Populator

## Configuration

Create a file called `private.json` as a sibling to `main.py` and populate it as follows:

```json
{
  "AIRTABLE_API_KEY": "my_key_from_https://airtable.com/account",
  "APP_PATH": "stuff_after_https://api.airtable.com/v0/_including_slash_in_the_middle_but_not_trailing",
  "LDAP_HOST": "ldap.my.edu",
  "LDAP_OC": "o=My University,c=US"
}
```

## Installation

Clone and then `[pipenv](https://pipenv.pypa.io/en/latest/) install`.

## Running

Configure as explained above, then look in `main.py`. `ldap.py` and `airtable.py` provide interfaces to those respective services.
