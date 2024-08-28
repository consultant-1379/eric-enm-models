#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2020
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import sys
from typing import List
from subprocess import CalledProcessError
from logger_utils import get_logger

from command_executor import execute_subprocess_command
from model_installer_strategy import ModelInstallerStrategy


class ModelInstaller:
    """
    Class to install relevant model RPMs from the zypper cache
    """

    def __init__(self, deploy_file):
        self.deploy_file = deploy_file
        self.logger = get_logger(self.__class__.__name__)

    def _install_model_rpms(self, rpms: List):
        """
        Install supplied model RPMs

        :param   rpms - A list of model RPMs to install
        :return: Boolean indicicating if install has completed succesfully
        """
        install_command = ['zypper', 'in', '-y']
        install_command.extend(rpms)

        try:
            execute_subprocess_command(install_command)
            self.logger.info("Model RPMs installed successfully")
        except CalledProcessError as zypper_error:
            self.logger.error(f"Model RPMs install failed: {zypper_error.stderr}")
            raise SystemExit(2) from zypper_error

    def install(self):
        """
        Gets the models to deploy and installs them

        :return: None
        """
        self.logger.info('Starting installation of model RPMs...')
        model_rpms_to_install = ModelInstallerStrategy.get_models_to_deploy(self.deploy_file)
        self.logger.debug('RPMs being installed: %s', model_rpms_to_install)
        self.logger.info('RPMs to be installed count: %s', len(model_rpms_to_install))

        self._install_model_rpms(model_rpms_to_install)
        self.logger.info("Finished install of model RPMs...")


if __name__ == '__main__':
    deployment_file = sys.argv[1]
    model_installer = ModelInstaller(deployment_file)
    model_installer.install()
