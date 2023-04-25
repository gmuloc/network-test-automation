# pylint: skip-file
"""
Tests for anta.tests.hardware.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from anta.tests.hardware import VerifyTransceiversManufacturers

# from tests.units.conftest import mocked_device


@pytest.mark.parametrize(
        "eos_data, side_effect, expected_result, expected_messages",
        [
            pytest.param(
                [
                    {
                        "xcvrSlots": {
                            "1": {
                                "mfgName": "Arista Networks",
                                "modelName": "QSFP-100G-DR",
                                "serialNum": "XKT203501340",
                                "hardwareRev": "21"
                            },
                            "2": {
                                "mfgName": "Arista Networks",
                                "modelName": "QSFP-100G-DR",
                                "serialNum": "XKT203501337",
                                "hardwareRev": "21"
                            }
                        }
                    }
                ],
                ['Arista Networks'],
                "success",
                [],
                id="success"
            ),
            pytest.param(
                [
                    {
                        "xcvrSlots": {
                            "1": {
                                "mfgName": "Arista Networks",
                                "modelName": "QSFP-100G-DR",
                                "serialNum": "XKT203501340",
                                "hardwareRev": "21"
                            },
                            "2": {
                                "mfgName": "Arista Networks",
                                "modelName": "QSFP-100G-DR",
                                "serialNum": "XKT203501337",
                                "hardwareRev": "21"
                            }
                        }
                    }
                ],
                ['Arista'],
                "failure",
                ['The following interfaces have transceivers from unauthorized manufacturers', "{'1': 'Arista Networks', '2': 'Arista Networks'}"],
                id="failure"
            ),
        ],
)
# @pytest.mark.usefixtures("mocked_device")
def test_VerifyTransceiversManufacturers(
    mocked_device: MagicMock,
    eos_data: List[Dict[str, str]],
    side_effect: Any,
    expected_result: str,
    expected_messages: List[str],
) -> None:
    test = VerifyTransceiversManufacturers(mocked_device, eos_data=eos_data)
    asyncio.run(test.test(manufacturers=side_effect))

    logging.warrning(f"mocked device is: {mocked_device}")
    logging.warrning(f"test input is: {side_effect}")
    logging.warrning(f"test result is: {test.result}")

    assert test.name == "verify_transceivers_manufacturers"
    assert test.categories == ["hardware"]
    assert test.result.test == "verify_transceivers_manufacturers"
    assert str(test.result.name) == mocked_device.name
    assert test.result.result == expected_result
    assert test.result.messages == expected_messages
