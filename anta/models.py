"""
Models to define a TestStructure
"""
from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractclassmethod, abstractmethod
from typing import Any

from aioeapi import EapiCommandError
from httpx import ConnectError, HTTPError
from pydantic import BaseModel

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tools import exc_to_str


class AntaTestCommand(BaseModel):
    """Class to define a test command with its API version

    Attributes:
        command(str): Test command
        version(str): eAPI version - default is latest
        ofmt(str):  eAPI output - json or text - default is json
    """

    command: str
    version: str = "latest"
    ofmt: str = "json"


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
    # ignoring mypy issue
    # https://github.com/python/mypy/issues/1362
    @property  # type: ignore
    @abstractclassmethod
    def name(cls) -> str:  # sourcery skip: instance-method-first-arg-name
        """Test Name"""

    @property  # type: ignore
    @abstractclassmethod
    def description(cls) -> str:  # sourcery skip: instance-method-first-arg-name
        """Test Description"""

    @property  # type: ignore
    @abstractclassmethod
    def categories(cls) -> list[str]:  # sourcery skip: instance-method-first-arg-name
        """Test Categories"""

    @property  # type: ignore
    @abstractclassmethod
    def commands(
        cls,
    ) -> list[AntaTestCommand]:  # sourcery skip: instance-method-first-arg-name
        """Test Commands"""

    # TODO test_filters optional
    @property  # type: ignore
    @classmethod
    def test_filters(cls) -> list[str]:  # sourcery skip: instance-method-first-arg-name
        """Test Filters

        for instance - supported platforms, ...
        """

    def __init__(
        self,
        device: InventoryDevice,
        eos_data: list[dict[Any, Any]] | None = None,
        labels: list[str] | None = None,
    ):
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.device = device
        self.result = TestResult(name=device.name, test=self.name)
        self.labels = labels or []
        self.eos_data = eos_data or []
        # TODO - check if we do this
        # self.id = ?

    async def _collect(self) -> None:
        """
        Private collection methids used in anta_assert to handle collection failures

        it calls the user defined collect coroutine
        """
        self.logger.debug(
            f"No data for test {self.name} for device {self.device.name}: running collect"
        )
        try:
            await self.collect()
            self.logger.debug(
                f"Data collected for test {self.name} for device {self.device.name}!"
            )
        except EapiCommandError as e:
            self.logger.error(f"Command failed on {self.device.name}: {e.errmsg}")
            self.result.is_error(exc_to_str(e))
        except (HTTPError, ConnectError) as e:
            self.logger.error(
                f"Cannot connect to device {self.device.name}: {type(e).__name__}{exc_to_str(e)}"
            )
            self.result.is_error(exc_to_str(e))
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Exception raised while collecting data for test {self.name} (on device {self.device.name}) - {exc_to_str(e)}"
            )
            self.logger.debug(traceback.format_exc())
            self.result.is_error(exc_to_str(e))

    @abstractmethod
    async def collect(self) -> None:
        """
        This method MUST be implemented for an AntaTest
        The expectation is that it is an asyncio method

        TODO

        Raises if anything fail
        """

    async def anta_assert(
        self,
        eos_data: list[dict[Any, Any]] | None = None,
        **kwargs: dict[str, Any],
    ) -> TestResult:
        """
        This method will call assert

        Returns:
            TestResult: self.result, populated with the correct exit status
        """
        # TODO maybe_skip ?

        # Data
        if eos_data:
            self.eos_data = eos_data

        # No test data is present, try to collect
        if not self.eos_data:
            await self._collect()
            if self.result.result != "unset":
                return self.result

        self.logger.debug(
            f"Running asserts for test {self.name} for device {self.device.name}: running collect"
        )
        try:
            self.asserts(**kwargs)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Exception raised during 'assert' for test {self.name} (on device {self.device.name}) - {exc_to_str(e)}"
            )
            self.logger.debug(traceback.format_exc())
            self.result.is_error(exc_to_str(e))
        return self.result

    @abstractmethod
    def asserts(self) -> None:
        """
        This abstract method is the core of the test.
        It MUST set the correct status of self.result with the appropriate error messages
        """
