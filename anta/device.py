# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Device Abstraction Module."""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Literal

import asyncssh
from aiocache import Cache
from aiocache.plugins import HitMissRatioPlugin
from aioeapi import Device, EapiCommandError
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, HTTPError

from anta import __DEBUG__
from anta.models import AntaCommand
from anta.tools.misc import anta_log_exception, exc_to_str

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

logger = logging.getLogger(__name__)


class AntaDevice(ABC):
    """Abstract class representing a device in ANTA.

    An implementation of this class must override the abstract coroutines `_collect()` and
    `refresh()`.

    Attributes
    ----------
        name: Device name
        is_online: True if the device IP is reachable and a port can be open
        established: True if remote command execution succeeds
        hw_model: Hardware model of the device
        tags: List of tags for this device
        cache: In-memory cache from aiocache library for this device (None if cache is disabled)
        cache_locks: Dictionary mapping keys to asyncio locks to guarantee exclusive access to the cache if not disabled
    """

    def __init__(self, name: str, tags: list[str] | None = None, disable_cache: bool = False) -> None:
        """Return an instance of AntaDevice.

        Args:
        ----
        name: Device name
        tags: List of tags for this device
        disable_cache: Disable caching for all commands for this device. Defaults to False.
        """
        self.name: str = name
        self.hw_model: str | None = None
        self.tags: list[str] = tags if tags is not None else []
        self.is_online: bool = False
        self.established: bool = False
        self.cache: Cache | None = None
        self.cache_locks: defaultdict[str, asyncio.Lock] | None = None

        # Initialize cache if not disabled
        if not disable_cache:
            self._init_cache()

    def _init_cache(self) -> None:
        """Initialize cache for the device, can be overriden by subclasses to manipulate how it works."""
        self.cache = Cache(cache_class=Cache.MEMORY, ttl=60, namespace=self.name, plugins=[HitMissRatioPlugin()])
        self.cache_locks = defaultdict(asyncio.Lock)

    @property
    def cache_statistics(self) -> dict[str, Any] | None:
        """Return the device cache statistics for logging purposes."""
        # Need to ignore pylint no-member as Cache is a proxy class and pylint is not smart enough
        # https://github.com/pylint-dev/pylint/issues/7258
        if self.cache is not None:
            stats = getattr(self.cache, "hit_miss_ratio", {"total": 0, "hits": 0, "hit_ratio": 0})
            return {"total_commands_sent": stats["total"], "cache_hits": stats["hits"], "cache_hit_ratio": f"{stats['hit_ratio'] * 100:.2f}%"}
        return None

    def __rich_repr__(self) -> Iterator[tuple[str, Any]]:
        """Implement Rich Repr Protocol.

        https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol.
        """
        yield "name", self.name
        yield "tags", self.tags
        yield "hw_model", self.hw_model
        yield "is_online", self.is_online
        yield "established", self.established
        yield "disable_cache", self.cache is None

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """AntaDevice equality depends on the class implementation."""

    @abstractmethod
    async def _collect(self, command: AntaCommand) -> None:
        """Collect device command output.

        This abstract coroutine can be used to implement any command collection method
        for a device in ANTA.

        The `_collect()` implementation needs to populate the `output` attribute
        of the `AntaCommand` object passed as argument.

        If a failure occurs, the `_collect()` implementation is expected to catch the
        exception and implement proper logging, the `output` attribute of the
        `AntaCommand` object passed as argument would be `None` in this case.

        Args:
        ----
        command: the command to collect
        """

    async def collect(self, command: AntaCommand) -> None:
        """Collect the output for a specified command.

        When caching is activated on both the device and the command,
        this method prioritizes retrieving the output from the cache. In cases where the output isn't cached yet,
        it will be freshly collected and then stored in the cache for future access.
        The method employs asynchronous locks based on the command's UID to guarantee exclusive access to the cache.

        When caching is NOT enabled, either at the device or command level, the method directly collects the output
        via the private `_collect` method without interacting with the cache.

        Args:
        ----
        command (AntaCommand): The command to process.
        """
        # Need to ignore pylint no-member as Cache is a proxy class and pylint is not smart enough
        # https://github.com/pylint-dev/pylint/issues/7258
        if self.cache is not None and self.cache_locks is not None and command.use_cache:
            async with self.cache_locks[command.uid]:
                cached_output = await self.cache.get(command.uid)  # pylint: disable=no-member

                if cached_output is not None:
                    logger.debug("Cache hit for %s on %s", command.command, self.name)
                    command.output = cached_output
                else:
                    await self._collect(command=command)
                    await self.cache.set(command.uid, command.output)  # pylint: disable=no-member
        else:
            await self._collect(command=command)

    async def collect_commands(self, commands: list[AntaCommand]) -> None:
        """Collect multiple commands.

        Args:
        ----
        commands: the commands to collect
        """
        await asyncio.gather(*(self.collect(command=command) for command in commands))

    @abstractmethod
    async def refresh(self) -> None:
        """Update attributes of an AntaDevice instance.

        This coroutine must update the following attributes of AntaDevice:
            - `is_online`: When the device IP is reachable and a port can be open
            - `established`: When a command execution succeeds
            - `hw_model`: The hardware model of the device
        """

    async def copy(self, sources: list[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """Copy files to and from the device, usually through SCP.

        It is not mandatory to implement this for a valid AntaDevice subclass.

        Args:
        ----
        sources: List of files to copy to or from the device.
        destination: Local or remote destination when copying the files. Can be a folder.
        direction: Defines if this coroutine copies files to or from the device.
        """
        # pylint: disable=unused-argument
        # ruff: noqa: ARG002
        msg = f"copy() method has not been implemented in {self.__class__.__name__} definition"
        raise NotImplementedError(msg)


class AsyncEOSDevice(AntaDevice):
    """Implementation of AntaDevice for EOS using aio-eapi.

    Attributes
    ----------
    name: Device name
    is_online: True if the device IP is reachable and a port can be open
    established: True if remote command execution succeeds
    hw_model: Hardware model of the device
    tags: List of tags for this device
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        name: str | None = None,
        enable: bool = False,
        enable_password: str | None = None,
        port: int | None = None,
        ssh_port: int | None = 22,
        tags: list[str] | None = None,
        timeout: float | None = None,
        insecure: bool = False,
        proto: Literal["http", "https"] = "https",
        disable_cache: bool = False,
    ) -> None:
        """Return an instance of AsyncEOSDevice.

        Args:
        ----
        host: Device FQDN or IP
        username: Username to connect to eAPI and SSH
        password: Password to connect to eAPI and SSH
        name: Device name
        enable: Device needs privileged access
        enable_password: Password used to gain privileged access on EOS
        port: eAPI port. Defaults to 80 is proto is 'http' or 443 if proto is 'https'.
        ssh_port: SSH port
        tags: List of tags for this device
        timeout: Timeout value in seconds for outgoing connections. Default to 10 secs.
        insecure: Disable SSH Host Key validation
        proto: eAPI protocol. Value can be 'http' or 'https'
        disable_cache: Disable caching for all commands for this device. Defaults to False.
        """
        # pylint: disable=too-many-arguments
        # ruff: noqa: PLR0913
        if name is None:
            name = f"{host}{f':{port}' if port else ''}"
        super().__init__(name, tags, disable_cache)
        self.enable = enable
        self._enable_password = enable_password
        self._session: Device = Device(host=host, port=port, username=username, password=password, proto=proto, timeout=timeout)

        ssh_params: dict[str, Any] = {}
        if insecure:
            ssh_params["known_hosts"] = None
        self._ssh_opts: SSHClientConnectionOptions = SSHClientConnectionOptions(host=host, port=ssh_port, username=username, password=password, **ssh_params)

    def __rich_repr__(self) -> Iterator[tuple[str, Any]]:
        """Implement Rich Repr Protocol.

        https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol.
        """
        yield from super().__rich_repr__()
        yield ("host", self._session.host)
        yield ("eapi_port", self._session.port)
        yield ("username", self._ssh_opts.username)
        yield ("enable", self.enable)
        yield ("insecure", self._ssh_opts.known_hosts is None)
        if __DEBUG__:
            _ssh_opts = vars(self._ssh_opts).copy()
            _ssh_opts["password"] = _ssh_opts["kwargs"]["password"] = "<removed>"
            yield ("_session", vars(self._session))
            yield ("_ssh_opts", _ssh_opts)

    def __eq__(self, other: object) -> bool:
        """Two AsyncEOSDevice objects are equal if the hostname and the port are the same.

        This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        return self._session.host == other._session.host and self._session.port == other._session.port if isinstance(other, AsyncEOSDevice) else False

    async def _collect(self, command: AntaCommand) -> None:
        """Collect device command output from EOS using aio-eapi.

        Supports outformat `json` and `text` as output structure.
        Gain privileged access using the `enable_password` attribute
        of the `AntaDevice` instance if populated.

        Args:
        ----
        command: the command to collect
        """
        try:
            commands = []
            if self.enable and self._enable_password is not None:
                commands.append(
                    {
                        "cmd": "enable",
                        "input": str(self._enable_password),
                    },
                )
            elif self.enable:
                # No password
                commands.append({"cmd": "enable"})
            if command.revision:
                commands.append({"cmd": command.command, "revision": command.revision})
            else:
                commands.append({"cmd": command.command})
            response = await self._session.cli(
                commands=commands,
                ofmt=command.ofmt,
                version=command.version,
            )
            # remove first dict related to enable command
            # only applicable to json output
            if command.ofmt in ["json", "text"]:
                # selecting only our command output
                response = response[-1]
            command.output = response
            logger.debug("%s: %s", self.name, command)

        except EapiCommandError as e:
            message = f"Command '{command.command}' failed on {self.name}"
            anta_log_exception(e, message, logger)
            command.failed = e
        except (HTTPError, ConnectError) as e:
            message = f"Cannot connect to device {self.name}"
            anta_log_exception(e, message, logger)
            command.failed = e
        except Exception as e:  # pylint: disable=broad-exception-caught
            message = f"Exception raised while collecting command '{command.command}' on device {self.name}"
            anta_log_exception(e, message, logger)
            command.failed = e
            logger.debug(command)

    async def refresh(self) -> None:
        """Update attributes of an AsyncEOSDevice instance.

        This coroutine must update the following attributes of AsyncEOSDevice:
        - is_online: When a device IP is reachable and a port can be open
        - established: When a command execution succeeds
        - hw_model: The hardware model of the device
        """
        logger.debug("Refreshing device %s", self.name)
        self.is_online = await self._session.check_connection()
        if self.is_online:
            command: str = "show version"
            hw_mode_key: str = "modelName"
            try:
                response = await self._session.cli(command=command)
            except EapiCommandError as e:
                logger.warning("Cannot get hardware information from device %s: %s", self.name, e.errmsg)

            except (HTTPError, ConnectError) as e:
                logger.warning("Cannot get hardware information from device %s: %s", self.name, exc_to_str(e))

            else:
                if hw_mode_key in response:
                    self.hw_model = response[hw_mode_key]
                else:
                    logger.warning("Cannot get hardware information from device %s: cannot parse '%s'", self.name, command)

        else:
            logger.warning("Could not connect to device %s: cannot open eAPI port", self.name)

        self.established = bool(self.is_online and self.hw_model)

    async def copy(self, sources: list[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """Copy files to and from the device using asyncssh.scp().

        Args:
        ----
        sources: List of files to copy to or from the device.
        destination: Local or remote destination when copying the files. Can be a folder.
        direction: Defines if this coroutine copies files to or from the device.
        """
        async with asyncssh.connect(
            host=self._ssh_opts.host,
            port=self._ssh_opts.port,
            tunnel=self._ssh_opts.tunnel,
            family=self._ssh_opts.family,
            local_addr=self._ssh_opts.local_addr,
            options=self._ssh_opts,
        ) as conn:
            src: list[tuple[SSHClientConnection, Path]] | list[Path]
            dst: tuple[SSHClientConnection, Path] | Path
            if direction == "from":
                src = [(conn, file) for file in sources]
                dst = destination
                for file in sources:
                    logger.info("Copying '%s' from device %s to '%s' locally", file, self.name, destination)
            elif direction == "to":
                src = sources
                dst = (conn, destination)
                for file in sources:
                    logger.info("Copying '%s' to device %s to '%s' remotely", file, self.name, destination)
            else:
                logger.critical("'direction' argument to copy() fonction is invalid: %s", direction)
                return
            await asyncssh.scp(src, dst)
