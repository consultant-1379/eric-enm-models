"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
from subprocess import CalledProcessError

from pytest import raises

from command_executor import execute_subprocess_command, call_subprocess_command


class TestCommandExecutor:
    """
    Test class for script `modeling_utils.command_executor`.
    """

    successful_command = ["echo"]
    failure_command = ["ls", "unknownFile"]

    def test_execute_command_successful(self):
        execute_subprocess_command(self.successful_command)
        execute_subprocess_command(self.successful_command, True)

    def test_execute_command_failure(self):
        with raises(CalledProcessError) as error:
            execute_subprocess_command(self.failure_command)
        assert 2 == error.value.args[0]

        with raises(CalledProcessError) as error:
            execute_subprocess_command(self.failure_command, True)
        assert 2 == error.value.args[0]

    def test_call_command_successful(self):
        assert 0 == call_subprocess_command(self.successful_command)

    def test_call_command_failure(self):
        assert 2 == call_subprocess_command(self.failure_command)
