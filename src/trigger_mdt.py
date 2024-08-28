#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2020
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import datetime
import shutil
import time
from os import environ, path, makedirs

from logger_utils import get_logger
from command_executor import call_subprocess_command


class MdtTool:
    """
    Class to prepare model RPMs, trigger MDT installation and perform a cleanup on success.
    """
    _LOCAL_TO_BE_INSTALLED_DIR = "/etc/opt/ericsson/models/toBeInstalled"
    _MDC_CLASSPATH = '/opt/ericsson/ERICmodeldeploymentclient/lib/*'
    _MDC_MAINCLASS = 'com.ericsson.oss.itpf.modeling.model.deployment.client.main.ModelDeployment' \
                     'ClientStart'
    _MODELLING_MOUNT_POINT = '/etc/opt/ericsson/ERICmodeldeployment/'
    _MODEL_DEPLOYMENT_SERVICE_FILE = _MODELLING_MOUNT_POINT + 'data/ModelDeploymentService'
    _SLEEP_INTERVAL = 5

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def _copy_model_jars_to_mdt_mount(self, local_to_be_installed_dir: str, mdt_models_dir: str):
        """
        Copies model jars to the MDT mount and verifies the status of the operation.

        :param str local_to_be_installed_dir: directory path containing jars to be deployed
        :param  str mdt_models_dir: directory on mountpoint to transfer jars to
        :return: None
        """
        try:
            self.logger.info("Copying model jars to the MDT directory...")
            makedirs(path.dirname(mdt_models_dir), exist_ok=True)
            shutil.copytree(local_to_be_installed_dir, mdt_models_dir)
        except OSError as os_error:
            self.logger.error('Failed to copy model jars to the MDT directory %s '
                              'with error %s', {mdt_models_dir}, {str(os_error)})
            raise SystemExit(2) from os_error

    def _wait_for_model_deployment_service_file(self, service_file_path: str):
        """
        Queries the MDT mount repeatedly for the ModelDeploymentService file.

        :param str service_file_path: path to the ModelDeploymentService rmi stub file
        :return: None
        """
        wait = 0
        self.logger.info('Waiting for ModelDeploymentService file to become available...')
        while not path.exists(service_file_path):
            warning_message = \
                f'ModelDeploymentService file not currently available. ' \
                f'Retrying in {self._SLEEP_INTERVAL} seconds (waited {wait} seconds so far)...'
            self.logger.warning(warning_message)
            wait += self._SLEEP_INTERVAL
            time.sleep(self._SLEEP_INTERVAL)
        self.logger.info('Found ModelDeploymentService file. '
                         '(Took %i seconds) Starting ModelDeploymentClient...', wait)

    def _invoke_mdt_via_model_deployment_client(self, mdt_models_dir: str):
        """
        Invokes MDT using the Model Deployment Client repeatedly and waits on the blocking call
        until MDT executes successfully. Upon successful MDT execution, places a marker file.

        :param   mdt_models_dir - mountpoint directory containing model jars to be installed
        :return: None
        """
        returncode = 1
        while returncode != 0:
            java_command = ['java', '-cp', self._MDC_CLASSPATH,
                            self._MDC_MAINCLASS, mdt_models_dir]
            returncode = call_subprocess_command(java_command)
            time.sleep(self._SLEEP_INTERVAL)
        self.logger.info('Successfully completed Model Deployment Tool execution.')

    def _clean_up_old_model_jars(self, to_be_installed_dir: str):
        """
        Removes old model jars from the relevant models directory on the MDT mount if they exist.

        :param str to_be_installed_dir: mountpoint directory that contained the model jars to deploy
        :return: None
        """
        if path.exists(to_be_installed_dir):
            try:
                shutil.rmtree(to_be_installed_dir)
                success_log = 'Successfully removed model jars from the staging directory: {0}. ' \
                              'Terminating container...' \
                    .format(str(to_be_installed_dir))
                self.logger.info(success_log)
            except OSError as os_error:
                error_log = 'Failed to remove models from the MDT mount with error {0}' \
                    .format(str(os_error))
                self.logger.error(error_log)
                raise SystemExit(2) from os_error

    def trigger_mdt(self):
        """
        Main function for trigger mdt

        :return: None
        """
        try:
            current_time = time.time()
            timestamp = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d_%H-%M-%S')
            to_be_installed_dir = self._MODELLING_MOUNT_POINT + 'data/execution/toBeInstalled/'\
                                  + environ['MODELS_TYPE']
            mdt_models_dir = to_be_installed_dir + '/' + timestamp

            self._copy_model_jars_to_mdt_mount(self._LOCAL_TO_BE_INSTALLED_DIR, mdt_models_dir)
            if path.exists(mdt_models_dir):
                self._wait_for_model_deployment_service_file(self._MODEL_DEPLOYMENT_SERVICE_FILE)
                self._invoke_mdt_via_model_deployment_client(mdt_models_dir)
                self._clean_up_old_model_jars(to_be_installed_dir)
        except Exception as error:
            self.logger.error('Error encountered when triggering MDT.'
                              'Error message: %s', {str(error)})


if __name__ == '__main__':
    mdt_tool = MdtTool()
    mdt_tool.trigger_mdt()
