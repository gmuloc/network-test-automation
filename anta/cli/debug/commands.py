#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable = redefined-outer-name

"""
Commands for Anta CLI to run debug commands.
"""

import asyncio
import logging

import click
from rich.console import Console

from anta.cli.debug.utils import RunArbitraryCommand
from anta.cli.utils import setup_logging
from anta.inventory import AntaInventory
from anta.models import AntaTestCommand

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option('--command', '-c', type=str, required=True, help='Command to run on EOS using eAPI')
@click.option('--ofmt', type=click.Choice(['text', 'json']), default='json', help='eAPI format to use. can be text or json')
@click.option('--api-version', '--version', type=str, default='latest', help='Version of the command through eAPI')
@click.option('--device', '-d', type=str, required=True, help='Device from inventory to use')
@click.option('--log-level', '--log', help='Logging level of the command', default='warning')
def run_cmd(ctx: click.Context, command: str, ofmt: str, api_version: str, device: str, log_level: str) -> None:
    """Run arbitrary command to an EOS device and get result using eAPI"""
    # pylint: disable=too-many-arguments
    console = Console()
    setup_logging(level=log_level)

    inventory_anta = AntaInventory(
        inventory_file=ctx.obj['inventory'],
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        enable_password=ctx.obj['enable_password']
    )

    device_anta = [inventory_device for inventory_device in inventory_anta.get_inventory() if inventory_device.name == device][0]

    logger.info(f'receive device from inventory: {device_anta}')

    console.print(f'run command [green]{command}[/green] on [red]{device}[/red]')

    run_command = RunArbitraryCommand(device=device_anta)
    run_command.instance_commands = [AntaTestCommand(command=command, ofmt=ofmt, version=api_version)]
    asyncio.run(run_command.collect())
    result = run_command.instance_commands[0].output
    console.print(result)
