"""
Models to define a TestStructure
"""

from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from copy import deepcopy
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, List, Optional, TypeVar, Union, cast

from pydantic import BaseModel

from anta.result_manager.models import TestResult
from anta.tools.misc import exc_to_str

if TYPE_CHECKING:
    from anta.inventory.models import InventoryDevice

F = TypeVar("F", bound=Callable[..., Any])


class AntaTestCommand(BaseModel):
    """Class to define a test command with its API version

    Attributes:
        command(str): Test command
        version(str): eAPI version - default is latest
        ofmt(str):  eAPI output - json or text - default is json
        output: collected output either dict for json or str for text
    """

    command: str
    version: str = "latest"
    ofmt: str = "json"
    output: Optional[Union[Dict[Any, Any], str]]
    command_exc: Union[str, List[str], None] = None

    def __init__(self, **kwargs: Dict[str, Any]):
        """Class constructor"""
        super().__init__(**kwargs)
        if not hasattr(object, 'command_exc'):
            object.__setattr__(self, 'command_exc', [self.command])


class AntaTestDynamiCommand(AntaTestCommand):
    """
    Class to define a test command with dynamic parameters

    TODO: make a better doc
    supports commands like show interface <Eth1> where Eth1 is provided during test

    Args:
        AntaTest (_type_): _description_

    Raises:
        NotImplementedError: _description_

    Returns:
        _type_: _description_
    """
    # command_base: str
    parameters: List[Dict[Any, Any]] = [{}]

    def __init__(self, **kwargs: Dict[str, Any]):
        """Class constructor"""
        super().__init__(**kwargs)
        object.__setattr__(self, 'command_exc', [str(self.command).format(**param) for param in self.parameters])


class AntaTestFilter(ABC):
    """Class to define a test Filter"""

    # pylint: disable=too-few-public-methods

    @abstractmethod
    def should_skip(
        self,
        device: InventoryDevice,
        result: TestResult,
        *args: list[Any],
        **kwagrs: dict[str, Any],
    ) -> bool:
        """
        Sets the TestResult status to skip with the appropriate skip message

        Returns:
            bool: True if the test should be skipped, False otherwise
        """


class AntaTest(ABC):
    """Abstract class defining a test for Anta

    The goal of this class is to handle the heavy lifting and make
    writing a test as simple as possible.

    TODO - complete doctstring with example
    """

    # Mandatory class attributes
    # TODO - find a way to tell mypy these are mandatory for child classes - maybe Protocol
    name: ClassVar[str]
    description: ClassVar[str]
    categories: ClassVar[list[str]]
    commands: ClassVar[list[Union[AntaTestCommand, AntaTestDynamiCommand]]]

    # Optional class attributes
    test_filters: ClassVar[list[AntaTestFilter]]

    def __init__(
        self,
        device: InventoryDevice,
        eos_data: list[dict[Any, Any] | str] | None = None,
        labels: list[str] | None = None,
    ):
        """Class constructor"""
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.logger.setLevel(level="INFO")
        self.device = device
        self.result = TestResult(name=device.name, test=self.name)
        self.labels = labels or []
        # TODO - check optimization
        self.instance_commands = deepcopy(self.__class__.commands)
        if eos_data is not None:
            self.logger.debug("Test initialized with input data")
            self.save_commands_data(eos_data)

        # TODO - check if we do this
        # self.id = ?

    def save_commands_data(self, eos_data: list[dict[Any, Any] | str]) -> None:
        """Called at init or at test execution time"""
        for index, data in enumerate(eos_data or []):
            self.instance_commands[index].output = data

    def all_data_collected(self) -> bool:
        """returns True if output is populated for every command"""
        return all(command.output is not None for command in self.instance_commands)

    def __init_subclass__(cls) -> None:
        """
        Verify that the mandatory class attributes are defined
        """
        mandatory_attributes = ["name", "description", "categories", "commands"]
        for attr in mandatory_attributes:
            if not hasattr(cls, attr):
                raise NotImplementedError(
                    f"Class {cls} is missing required class attribute {attr}"
                )

    async def collect(self) -> None:
        """
        Private collection methids used in anta_assert to handle collection failures

        it calls the collect co-routing define in InventoryDevice to collect ouput per command

        FIXME: to be tested and review
        """

        for command in self.instance_commands:
            command = await(self.device.collect(command=command))

    @staticmethod
    def anta_test(function: F) -> F:
        """
        Decorator for anta_test that handles injecting test data if given and collecting it using asyncio if missing
        """

        @wraps(function)
        async def wrapper(
            self: AntaTest,
            eos_data: list[dict[Any, Any] | str] | None = None,
            **kwargs: dict[str, Any],
        ) -> TestResult:
            """
            This method will call assert

            Returns:
                TestResult: self.result, populated with the correct exit status
            """
            # TODO maybe_skip ?

            # Data
            if eos_data is not None:
                self.logger.debug("Test initialized with input data")
                self.save_commands_data(eos_data)

            # No test data is present, try to collect
            if not self.all_data_collected():
                await self.collect()
                if self.result.result != "unset":
                    return self.result

            self.logger.debug(
                f"Running asserts for test {self.name} for device {self.device.name}: running collect"
            )
            try:
                function(self, **kwargs)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.logger.error(
                    f"Exception raised during 'assert' for test {self.name} (on device {self.device.name}) - {exc_to_str(e)}"
                )
                self.logger.debug(traceback.format_exc())
                self.result.is_error(exc_to_str(e))
            return self.result

        return cast(F, wrapper)

    @abstractmethod
    def test(self) -> None:
        """
        This abstract method is the core of the test.
        It MUST set the correct status of self.result with the appropriate error messages
        """
