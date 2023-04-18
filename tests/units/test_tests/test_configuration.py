# pylint: skip-file
"""
Tests for anta.tests.configuration.py
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from httpx import HTTPError

from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyZeroTouch


[{"output":[{"mode": "disabled"}]}]

@pytest.mark.parametrize(
    "eos_data, side_effect, expected_result, expected_messages",
    [
        pytest.param([[{"mode": "disabled"}]], None, "success", [], id="success"),
        pytest.param(
            [[{"mode": "enabled"}]],
            None,
            "failure",
            ["ZTP is NOT disabled"],
            id="failure",
        ),
        # Hmmmm both errors do not return the same string ...
        # TODO: need to cover other exceptions like EapiCommandError
        # pytest.param(
        #     None, HTTPError("dummy"), "error", ["HTTPError (dummy)"], id="HTTP error"
        # ),
        # pytest.param(
        #     None, KeyError("dummy"), "error", ["KeyError ('dummy')"], id="Key error"
        # ),
    ],
)
def test_VerifyZeroTouch(
    mocked_device: MagicMock,
    eos_data: List[Dict[str, str]],
    side_effect: Any,
    expected_result: str,
    expected_messages: List[str],
) -> None:
    # TODO mock per command probably ..
    if eos_data:
        mocked_device.session.cli.return_value = eos_data[0]
    mocked_device.session.cli.side_effect = side_effect
    # TODO technically could avoid mocking to only test the assert part
    test = VerifyZeroTouch(mocked_device, eos_data=eos_data)
    test.logger.setLevel(level="DEBUG")
    asyncio.run(test.test())

    assert test.name == "verify_zerotouch"
    assert test.categories == ["configuration"]
    assert test.result.test == "verify_zerotouch"
    assert str(test.result.name) == mocked_device.name
    assert test.result.result == expected_result
    assert test.result.messages == expected_messages


@pytest.mark.parametrize(
    "eos_data, side_effect, expected_result, expected_messages",
    [
        pytest.param(
            [['', '']],
            None,
            # False,
            "success",
            [],
            id="success",
        ),
        pytest.param(
            [['blah', 'blah']],
            None,
            # False,
            "failure",
            ['blah', 'blah'],
            id="failure",
        ),
    ],
)
def test_VerifyRunningConfigDiffs(
    mocked_device: MagicMock,
    eos_data: List[str],
    side_effect: Any,
    expected_result: str,
    expected_messages: List[str],
) -> None:
    # TODO mock per command probably ..
    if eos_data:
        mocked_device.session.cli.return_value = eos_data[0]
    mocked_device.session.cli.side_effect = side_effect
    # TODO technically could avoid mocking to only test the assert part
    test = VerifyRunningConfigDiffs(mocked_device)
    asyncio.run(test.test())

    assert test.name == "verify_running_config_diffs"
    assert test.categories == ["configuration"]
    assert test.result.test == "verify_running_config_diffs"
    assert str(test.result.name) == mocked_device.name
    assert test.result.result == expected_result
    assert test.result.messages == expected_messages
