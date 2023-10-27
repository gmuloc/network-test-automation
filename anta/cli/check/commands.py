# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable = redefined-outer-name

"""
Commands for Anta CLI to run check commands.
"""
from __future__ import annotations

import logging

import click
from pydantic import ValidationError
from rich.pretty import pretty_repr

from anta.catalog import AntaCatalog
from anta.cli.console import console
from anta.cli.utils import parse_catalog
from anta.tools.misc import anta_log_exception

logger = logging.getLogger(__name__)


@click.command(no_args_is_help=True)
@click.pass_context
@click.option(
    "--catalog",
    "-c",
    show_envvar=True,
    help="Path to the tests catalog YAML file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, resolve_path=True),
    required=True,
    callback=parse_catalog,
)
def catalog(ctx: click.Context, catalog: AntaCatalog) -> None:
    """
    Check that the catalog is valid
    """
    logger.info(f"Checking syntax of catalog {ctx.obj['catalog_path']}")
    try:
        catalog.check()
        console.print(f"[bold][green]Catalog {ctx.obj['catalog_path']} is valid")
        console.print(pretty_repr(catalog.file))
    except ValidationError as e:
        console.print(f"[bold][red]Catalog {ctx.obj['catalog_path']} is invalid")
        anta_log_exception(e)
        ctx.exit(1)