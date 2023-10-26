# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.result_manager.__init__.py."""
from __future__ import annotations

import json
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any, Callable, ContextManager

import pytest

from anta.result_manager import ResultManager
from anta.result_manager.models import ListResult

if TYPE_CHECKING:
    from anta.custom_types import TestStatus
    from anta.result_manager.models import TestResult


class TestResultManager:
    """Test ResultManager class."""

    # not testing __init__ as nothing is going on there

    def test__len__(self, list_result_factory: Callable[[int], ListResult]) -> None:
        """Test __len__."""
        list_result = list_result_factory(3)
        result_manager = ResultManager()
        assert len(result_manager) == 0
        for i in range(3):
            result_manager.add_test_result(list_result[i])
            assert len(result_manager) == i + 1

    @pytest.mark.parametrize(
        ("starting_status", "test_status", "expected_status", "expected_raise"),
        [
            pytest.param("unset", "unset", "unset", nullcontext(), id="unset->unset"),
            pytest.param("unset", "success", "success", nullcontext(), id="unset->success"),
            pytest.param("unset", "error", "unset", nullcontext(), id="set error"),
            pytest.param("skipped", "skipped", "skipped", nullcontext(), id="skipped->skipped"),
            pytest.param("skipped", "unset", "skipped", nullcontext(), id="skipped, add unset"),
            pytest.param("skipped", "success", "success", nullcontext(), id="skipped, add success"),
            pytest.param("skipped", "failure", "failure", nullcontext(), id="skipped, add failure"),
            pytest.param("success", "unset", "success", nullcontext(), id="success, add unset"),
            pytest.param("success", "skipped", "success", nullcontext(), id="success, add skipped"),
            pytest.param("success", "success", "success", nullcontext(), id="success->success"),
            pytest.param("success", "failure", "failure", nullcontext(), id="success->failure"),
            pytest.param("failure", "unset", "failure", nullcontext(), id="failure->failure"),
            pytest.param("failure", "skipped", "failure", nullcontext(), id="failure, add unset"),
            pytest.param("failure", "success", "failure", nullcontext(), id="failure, add skipped"),
            pytest.param("failure", "failure", "failure", nullcontext(), id="failure, add success"),
            pytest.param("unset", "unknown", None, pytest.raises(ValueError, match=""), id="wrong status"),
        ],
    )
    def test__update_status(self, starting_status: TestStatus, test_status: TestStatus, expected_status: str, expected_raise: ContextManager) -> None:
        """Test ResultManager._update_status."""
        result_manager = ResultManager()
        result_manager.status = starting_status
        assert result_manager.error_status is False

        with expected_raise:
            result_manager._update_status(test_status)  # pylint: disable=protected-access
            if test_status == "error":
                assert result_manager.error_status is True
            else:
                assert result_manager.status == expected_status

    def test_add_test_result(self, test_result_factory: Callable[[int], TestResult]) -> None:
        """Test ResultManager.add_test_result."""
        result_manager = ResultManager()
        assert result_manager.status == "unset"
        assert result_manager.error_status is False
        assert len(result_manager) == 0

        # Add one unset test
        unset_test = test_result_factory(0)
        unset_test.result = "unset"
        result_manager.add_test_result(unset_test)
        assert result_manager.status == "unset"
        assert result_manager.error_status is False
        assert len(result_manager) == 1

        # Add one success test
        success_test = test_result_factory(1)
        success_test.result = "success"
        result_manager.add_test_result(success_test)
        assert result_manager.status == "success"
        assert result_manager.error_status is False
        assert len(result_manager) == 2

        # Add one error test
        error_test = test_result_factory(1)
        error_test.result = "error"
        result_manager.add_test_result(error_test)
        assert result_manager.status == "success"
        assert result_manager.error_status is True
        assert len(result_manager) == 3

        # Add one failure test
        failure_test = test_result_factory(1)
        failure_test.result = "failure"
        result_manager.add_test_result(failure_test)
        assert result_manager.status == "failure"
        assert result_manager.error_status is True
        assert len(result_manager) == 4

    def test_add_test_results(self, list_result_factory: Callable[[int], ListResult]) -> None:
        """Test ResultManager.add_test_results."""
        result_manager = ResultManager()
        assert result_manager.status == "unset"
        assert result_manager.error_status is False
        assert len(result_manager) == 0

        # Add three success tests
        success_list = list_result_factory(3)
        for test in success_list:
            test.result = "success"
        result_manager.add_test_results(success_list.root)
        assert result_manager.status == "success"
        assert result_manager.error_status is False
        assert len(result_manager) == 3

        # Add one error test and one failure
        error_failure_list = list_result_factory(2)
        error_failure_list[0].result = "error"
        error_failure_list[1].result = "failure"
        result_manager.add_test_results(error_failure_list.root)
        assert result_manager.status == "failure"
        assert result_manager.error_status is True
        assert len(result_manager) == 5

    @pytest.mark.parametrize(
        ("status", "error_status", "ignore_error", "expected_status"),
        [
            pytest.param("success", False, True, "success", id="no error"),
            pytest.param("success", True, True, "success", id="error, ignore error"),
            pytest.param("success", True, False, "error", id="error, do not ignore error"),
        ],
    )
    def test_get_status(self, status: TestStatus, error_status: bool, ignore_error: bool, expected_status: str) -> None:
        """Test ResultManager.get_status."""
        result_manager = ResultManager()
        result_manager.status = status
        result_manager.error_status = error_status

        assert result_manager.get_status(ignore_error=ignore_error) == expected_status

    @pytest.mark.parametrize(
        ("_format", "expected_raise"),
        [
            ("native", nullcontext()),
            ("json", nullcontext()),
            ("dummy", pytest.raises(ValueError, match="")),
        ],
    )
    def test_get_results(self, list_result_factory: Callable[[int], ListResult], _format: str, expected_raise: Any) -> None:
        """Test ResultManager.get_results."""
        result_manager = ResultManager()

        success_list = list_result_factory(3)
        for test in success_list:
            test.result = "success"
        result_manager.add_test_results(success_list.root)

        with expected_raise:
            res = result_manager.get_results(output_format=_format)
            if _format == "json":
                assert isinstance(res, str)
                # verifies it can be loaded as json
                json.loads(res)
            elif _format == "list":
                assert isinstance(res, list)
            elif _format == "native":
                assert isinstance(res, ListResult)

    # TODO
    # get_result_by_test
    # get_result_by_host
    # get_testcases
    # get_hosts
