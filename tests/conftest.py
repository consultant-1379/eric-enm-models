"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

Pytest file for generic test 'fixtures'.
"""
import pytest


@pytest.fixture(autouse=True)
def override_logger_rsyslog_call(fake_process):
    """
    Mock 'logger_utils' rsyslog call
    """
    fake_process.allow_unregistered(True)
    fake_process.register_subprocess(['/usr/bin/pgrep', 'rsyslogd'], returncode=0)
    fake_process.keep_last_process(True)
