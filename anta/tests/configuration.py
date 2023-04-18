"""
Test functions related to the device configuration
"""
from __future__ import annotations

import logging

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyZeroTouch(AntaTest):
    """
    Verifies ZeroTouch is disabled.
    """

    name = "verify_zerotouch"
    description = "Verifies ZeroTouch is disabled."
    categories = ["configuration"]
    commands = [AntaTestCommand(command="show zerotouch")]

    @AntaTest.anta_test
    def test(self) -> None:
        # TODO - easier way to access output ? / We need to make output[1] since we inject enable
        command_output = self.instance_commands[0].output[1]
        self.logger.info(f'dataset is: {command_output}')
        assert isinstance(command_output, dict)
        if command_output["mode"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("ZTP is NOT disabled")

class VerifyRunningConfigDiffs(AntaTest):
    """
    Verifies there is no difference between the running-config and the startup-config.
    """

    name = "verify_running_config_diffs"
    description = ""
    categories = ["configuration"]
    commands = [AntaTestCommand(command="show running-config diffs", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].output
        assert command_output is None or isinstance(command_output, str)
        self.logger.debug(f"command_output is {command_output}")
        if command_output is None:
            self.result.is_success()

        else:
            self.result.is_failure()
            for line in command_output.splitlines():
                self.result.is_failure(line)
        self.logger.debug(f"result is {self.result}")
