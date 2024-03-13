# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to multicast."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import Vlan
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate

class VerifyIGMPSnoopingVlans(AntaTest):
    """Verifies the IGMP snooping configuration for some VLANs."""

    name = "VerifyIGMPSnoopingVlans"
    description = "Verifies the IGMP snooping configuration for some VLANs."
    categories: ClassVar[list[str]] = ["multicast", "igmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip igmp snooping")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        vlans: dict[Vlan, bool]
        """Dictionary of VLANs with associated IGMP configuration status (True=enabled, False=disabled)"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        for vlan, enabled in self.inputs.vlans.items():
            if str(vlan) not in command_output["vlans"]:
                self.result.is_failure(f"Supplied vlan {vlan} is not present on the device.")
                continue

            igmp_state = command_output["vlans"][str(vlan)]["igmpSnoopingState"]
            if igmp_state != "enabled" if enabled else igmp_state != "disabled":
                self.result.is_failure(f"IGMP state for vlan {vlan} is {igmp_state}")


class VerifyIGMPSnoopingGlobal(AntaTest):
    """Verifies the IGMP snooping global configuration."""

    name = "VerifyIGMPSnoopingGlobal"
    description = "Verifies the IGMP snooping global configuration."
    categories: ClassVar[list[str]] = ["multicast", "igmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip igmp snooping")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        enabled: bool
        """Expected global IGMP snooping configuration (True=enabled, False=disabled)"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        igmp_state = command_output["igmpSnoopingState"]
        if igmp_state != "enabled" if self.inputs.enabled else igmp_state != "disabled":
            self.result.is_failure(f"IGMP state is not valid: {igmp_state}")
