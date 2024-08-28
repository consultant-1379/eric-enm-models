#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2020
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import logging
import subprocess
from logging import StreamHandler
from logging.handlers import SysLogHandler

"""
Utility script that creates a :class:`logging.Logger`.
"""


def get_logger(logger_name):
    """
    Creates a custom :class:`logging.Logger` object.

    :param   logger_name: Name of logger
    :return: :class:`logging.Logger` object
    """
    _enable_syslog()

    logging.basicConfig(
        level=logging.INFO,
        handlers=[_get_syslog_handler(),
                  _get_console_log_handler()])

    return logging.getLogger(logger_name)


def _enable_syslog():
    """
    Enables rsyslogd if it is not running.

    :return: None
    """
    if subprocess.call(['/usr/bin/pgrep', 'rsyslogd']) != 0:
        subprocess.call("/sbin/rsyslogd")


def _get_syslog_handler():
    """
    Creates a :class:`logging.handlers.SysLogHandler` that outputs logs
    to /var/log/messages provided that syslog is running.

    :param    None
    :return:  A :class:`logging.handlers.SysLogHandler` object
    """
    syslog_format = '(%(name)s:%(lineno)d) %(levelname)s - %(message)s'
    syslog_formatter = logging.Formatter(syslog_format)
    syslog_handler = SysLogHandler(address='/dev/log')
    syslog_handler.setFormatter(syslog_formatter)
    return syslog_handler


def _get_console_log_handler():
    """
    Creates a :class:`logging.StreamHandler` that outputs logs to the console.

    :param    None
    :return:  A :class:`logging.StreamHandler` object
    """
    console_log_format = '%(asctime)s (%(name)s:%(lineno)d) %(levelname)s - %(message)s'
    console_log_datetime_format = '%d-%b-%y %H:%M:%S'
    console_log_formatter = logging.Formatter(console_log_format, console_log_datetime_format)
    console_log_handler = StreamHandler()
    console_log_handler.setFormatter(console_log_formatter)
    return console_log_handler
