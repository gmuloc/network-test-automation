# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.runner.py."""

from __future__ import annotations

import logging
import resource
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta import logger
from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.runner import adjust_rlimit_nofile, main, prepare_tests

if TYPE_CHECKING:
    from typing import Any, Callable

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"


@pytest.mark.parametrize(
    ("test_inventory", "test_catalog"),
    [
        pytest.param("test_inventory_large.yml", "test_catalog_large.yml", id="large-50_devices-7688_tests"),
        pytest.param("test_inventory_medium.yml", "test_catalog_medium.yml", id="medium-6_devices-228_tests"),
        pytest.param("test_inventory.yml", "test_catalog.yml", id="small-3_devices-3_tests"),
    ],
    indirect=True,
)
def test_runner(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory, test_catalog: AntaCatalog, aio_benchmark: Callable[..., Any]) -> None:
    """Test and benchmark ANTA runner.

    caplog is the pytest fixture to capture logs.
    """
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)
    import time  # pylint: disable=C0415

    time.sleep(2)
    manager = ResultManager()
    aio_benchmark(main, manager, test_inventory, test_catalog)
