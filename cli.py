"""Command-line interface for PUL staff management system."""

# Standard library imports
from sys import exit as sys_exit
from typing import cast

# Third party imports
from click import confirm
from click import echo
from click import group
from click import option
from click import style

# Local imports
from main import App
from staff_management.staff_airtable import JSONDict


def load_config(use_production: bool) -> JSONDict:
    """Load configuration from private.json.

    Args:
        use_production: If True, use production base. If False, use test base.

    Returns:
        Configuration dict with PAT, BASE_ID, ALL_STAFF_TABLE_ID, REMOVAL_TABLE_ID
    """
    # Standard library imports
    from json import load

    with open("./private.json", "r") as f:
        config = cast(JSONDict, load(f))

    # Select test or production configuration
    env = "production" if use_production else "test"

    if env not in config:
        echo(style(f"Error: {env} configuration not found in private.json", fg="red"))
        echo(style("Expected structure:", fg="yellow"))
        echo("""{
  "test": {
    "PAT": "...",
    "BASE_ID": "...",
    "ALL_STAFF_TABLE_ID": "...",
    "REMOVAL_TABLE_ID": "..."
  },
  "production": {
    "PAT": "...",
    "BASE_ID": "...",
    "ALL_STAFF_TABLE_ID": "...",
    "REMOVAL_TABLE_ID": "..."
  }
}""")
        sys_exit(1)

    return cast(JSONDict, config[env])


@group()
@option("-p", "--production", is_flag=True, help="Use production Airtable base (default: test)")
@option("--csv", default="./Alpha Roster.csv", help="Path to CSV report file")
def cli(production: bool, csv: str) -> None:
    """PUL Staff Management - Sync CSV reports with Airtable.

    By default, operates on TEST Airtable base for safety.
    Use --production flag to work with production data.
    """
    # Store config in context for subcommands
    # Third party imports
    import click

    ctx = click.get_current_context()
    ctx.ensure_object(dict)
    ctx.obj["production"] = production
    ctx.obj["csv"] = csv

    # Show mode indicator
    mode = style("PRODUCTION", fg="red", bold=True) if production else style("TEST", fg="green", bold=True)
    echo(f"Mode: {mode}")


@cli.command()
@option("--verbose", "-v", is_flag=True, help="Show detailed information during checks")
def check(verbose: bool) -> None:
    """Run consistency checks between CSV and Airtable."""
    # Third party imports
    import click

    ctx = click.get_current_context()
    config = load_config(ctx.obj["production"])
    app = App(ctx.obj["csv"], config, verbose=verbose)

    echo("Checking for differences between the CSV roster and Airtable...")
    app.run_checks()
    echo(style("✓ Checks complete", fg="green"))


@cli.command()
@option("--verbose", "-v", is_flag=True, help="Show detailed field changes during sync")
def sync(verbose: bool) -> None:
    """Sync CSV report data to Airtable (interactive)."""
    # Third party imports
    import click

    ctx = click.get_current_context()
    config = load_config(ctx.obj["production"])

    if ctx.obj["production"]:
        if not confirm(style("You are in PRODUCTION mode. Continue?", fg="red", bold=True)):
            echo("Aborted.")
            return

    app = App(ctx.obj["csv"], config, verbose=verbose)

    echo("Syncing CSV data to Airtable...")
    app.sync_airtable_with_report()
    echo(style("✓ Sync complete", fg="green"))


@cli.command()
@option("--verbose", "-v", is_flag=True, help="Show detailed supervisor updates")
def update_supervisors(verbose: bool) -> None:
    """Update supervisor hierarchy (slow operation)."""
    # Third party imports
    import click

    ctx = click.get_current_context()
    config = load_config(ctx.obj["production"])
    app = App(ctx.obj["csv"], config, verbose=verbose)

    echo("Updating supervisor information...")
    echo(style("Warning: This operation is slow due to API rate limiting", fg="yellow"))

    app.update_supervisor_info()
    echo(style("✓ Supervisor info updated", fg="green"))


def main() -> None:
    """Entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
