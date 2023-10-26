# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.__init__."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.cli import anta
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from click.testing import CliRunner
    from pytest import CaptureFixture


def test_anta(click_runner: CliRunner) -> None:
    """Test anta main entrypoint."""
    result = click_runner.invoke(anta)
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_anta_help(click_runner: CliRunner) -> None:
    """Test anta --help."""
    result = click_runner.invoke(anta, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_anta_nrfu_help(click_runner: CliRunner) -> None:
    """Test anta nrfu --help."""
    result = click_runner.invoke(anta, ["nrfu", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta nrfu" in result.output


def test_anta_exec_help(click_runner: CliRunner) -> None:
    """Test anta exec --help."""
    result = click_runner.invoke(anta, ["exec", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta exec" in result.output


def test_anta_debug_help(click_runner: CliRunner) -> None:
    """Test anta debug --help."""
    result = click_runner.invoke(anta, ["debug", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta debug" in result.output


def test_anta_get_help(click_runner: CliRunner) -> None:
    """Test anta get --help."""
    result = click_runner.invoke(anta, ["get", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta get" in result.output


def test_anta_nrfu(capsys: CaptureFixture[str], click_runner: CliRunner) -> None:
    """Test anta nrfu table, catalog is given via env."""
    # TODO this test should mock device connections...
    env = default_anta_env()
    with capsys.disabled():
        result = click_runner.invoke(anta, ["nrfu", "table"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 0
    assert "ANTA Inventory contains 3 devices" in result.output


def test_anta_password_required(click_runner: CliRunner) -> None:
    """Test that password is provided."""
    env = default_anta_env()
    env.pop("ANTA_PASSWORD")
    result = click_runner.invoke(anta, ["get", "inventory"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 2
    assert "EOS password needs to be provided by using either the '--password' option or the '--prompt' option." in result.output


def test_anta_password(click_runner: CliRunner) -> None:
    """Test that password can be provided either via --password or --prompt."""
    env = default_anta_env()
    env.pop("ANTA_PASSWORD")
    result = click_runner.invoke(anta, ["--password", "blah", "get", "inventory"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 0
    result = click_runner.invoke(anta, ["--prompt", "get", "inventory"], input="password\npassword\n", env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 0


def test_anta_enable_password(click_runner: CliRunner) -> None:
    """Test that enable password can be provided either via --enable-password or --prompt."""
    env = default_anta_env()

    # Both enable and enable-password
    result = click_runner.invoke(anta, ["--enable", "--enable-password", "blah", "get", "inventory"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 0

    # enable and prompt y
    result = click_runner.invoke(anta, ["--enable", "--prompt", "get", "inventory"], input="y\npassword\npassword\n", env=env, auto_envvar_prefix="ANTA")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" in result.output
    assert result.exit_code == 0

    # enable and prompt N
    result = click_runner.invoke(anta, ["--enable", "--prompt", "get", "inventory"], input="N\n", env=env, auto_envvar_prefix="ANTA")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" not in result.output
    assert result.exit_code == 0

    result = click_runner.invoke(
        anta,
        ["--enable", "--enable-password", "blah", "--prompt", "get", "inventory"],
        input="y\npassword\npassword\n",
        env=env,
        auto_envvar_prefix="ANTA",
    )
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" not in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" not in result.output
    assert result.exit_code == 0

    # enabled-password without enable
    result = click_runner.invoke(anta, ["--enable-password", "blah", "get", "inventory"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 2
    assert "Providing a password to access EOS Privileged EXEC mode requires '--enable' option." in result.output


def test_anta_enable_alone(click_runner: CliRunner) -> None:
    """Test that enable can be provided either without enable-password."""
    env = default_anta_env()
    # enabled without enable-password and without prompt this is
    result = click_runner.invoke(anta, ["--enable", "get", "inventory"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 0


def test_disable_cache(click_runner: CliRunner) -> None:
    """Test that disable_cache is working on inventory."""
    env = default_anta_env()
    result = click_runner.invoke(anta, ["--disable-cache", "get", "inventory"], env=env, auto_envvar_prefix="ANTA")
    stdout_lines = result.stdout.split("\n")
    # All caches should be disabled from the inventory
    for line in stdout_lines:
        if "disable_cache" in line:
            assert "True" in line
    assert result.exit_code == 0
