#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2020
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import subprocess
from subprocess import PIPE
from typing import List, Optional

"""
Script to execute shell commands
"""


def execute_subprocess_command(command_to_run: List,
                               return_output: bool = False) -> Optional[bytes]:
    """
    Executes a command that is passed into this method.

    :param   command_to_run - The command to be executed.
    :param   return_output  - Should the command output be returned.
    :return: result of command or None.
    """
    if return_output:
        return subprocess.run(command_to_run, stdout=PIPE, stderr=PIPE, check=True).stdout
    subprocess.run(command_to_run, stdout=PIPE, stderr=PIPE, check=True)
    return None


def call_subprocess_command(command_to_run: List) -> int:
    """
    Executes a command that is passed into this method.

    :param   command_to_run - The command to be executed.
    :return: return code of executed command.
    """
    return subprocess.call(command_to_run)
