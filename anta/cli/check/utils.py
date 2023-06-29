#!/usr/bin/env python
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.check.commands module.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from rich import print_json
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint

from anta.inventory import AntaInventory
from anta.reporter import ReportJinja, ReportTable
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from anta.runner import main

logger = logging.getLogger(__name__)


def print_settings(console: Console, inventory: AntaInventory, catalog: str, template: Optional[str] = None) -> None:
    """Print ANTA settings before running tests"""
    message = f"Running ANTA tests with:\n- {inventory}\n- Tests catalog contains {len(catalog)} tests"
    if template:
        message += f"\n- Template: {template}"
    console.print(Panel.fit(message, style="cyan", title="[green]Settings"))


def check_run(inventory: AntaInventory, catalog: List[Tuple[Callable[..., TestResult], Dict[Any, Any]]], tags: Any) -> ResultManager:
    """Run ANTA tests"""
    if tags is not None:
        tags = tags.split(",") if "," in tags else [tags]

    results = ResultManager()
    asyncio.run(main(results, inventory, catalog, tags=tags))

    return results


def display_table(console: Console, results: ResultManager, group_by: Optional[str] = None, search: str = "") -> None:
    """Display result in a table"""
    reporter = ReportTable()
    if group_by is None:
        console.print(reporter.report_all(result_manager=results))
    elif group_by == "host":
        console.print(reporter.report_summary_hosts(result_manager=results, host=search))
    elif group_by == "test":
        console.print(reporter.report_summary_tests(result_manager=results, testcase=search))


def display_json(console: Console, results: ResultManager, output_file: Optional[str] = None) -> None:
    """Display result in a json format"""
    console.print(Panel("JSON results of all tests", style="cyan"))
    print_json(results.get_results(output_format="json"))
    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as fout:
            fout.write(results.get_results(output_format="json"))


def display_list(console: Console, results: ResultManager, output_file: Optional[str] = None) -> None:
    """Display result in a list"""
    console.print(Panel.fit("List results of all tests", style="cyan"))
    pprint(results.get_results(output_format="list"))
    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as fout:
            fout.write(str(results.get_results(output_format="list")))


def display_jinja(console: Console, results: ResultManager, template: str, output: Union[str, None] = None) -> None:
    """Display result based on template."""
    # console.print(Panel.fit(f"Custom report from {template}", style="cyan"))
    reporter = ReportJinja(template_path=template)
    json_data = json.loads(results.get_results(output_format="json"))
    report = reporter.render(json_data)
    console.print(report)
    if output is not None:
        with open(output, "w", encoding="utf-8") as file:
            file.write(report)
