#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import os
import sys
import pathlib
from typing import Tuple
from shutil import move

from logger_utils import get_logger
from command_executor import execute_subprocess_command


def validate_input_directories(model_jar_location: str):
    """
    Ensures that valid directories have been supplied to the script
    :param: model_jar_location - location of model jar
    :return: None
    """
    if len(model_jar_location) == 0:
        raise ValueError('No model directory supplied')

    if model_jar_location.endswith("/"):
        model_jar_location = model_jar_location[:-1]

    if not os.path.isdir(model_jar_location):
        raise ValueError(f'Supplied directory "{model_jar_location}" does not exist')

    if not model_jar_location.endswith("install") and not \
            model_jar_location.endswith("post_install"):
        raise ValueError(f"Model directories must end with 'install' or "
                         f"'post_install'. {model_jar_location} supplied")


def get_model_type() -> str:
    """
    Get 'MODELS_TYPE' env value or raise error if not set

    :return value of 'MODELS_TYPE' env variable
    """
    models_type_env_key = 'MODELS_TYPE'
    models_type = os.getenv(models_type_env_key)
    if models_type is not None and len(models_type) != 0:
        return models_type

    raise EnvironmentError('MODELS_TYPE environment variable not found')


def decode_rpm_name(source_rpm_information: bytes) -> Tuple[str, str]:
    """
    Decodes the rpm command output and returns the rpm name and version

    :param: source_rpm_information - rpm command output
    :return Tuple[rpm_name, rpm_version]
    """
    rpm_name = str(source_rpm_information.decode()).split('-')[0]
    rpm_version = str(source_rpm_information.decode()).split('-')[1]

    return rpm_name, rpm_version


class ModelLayoutTool:
    """
    This class is responsible for creating directory structure
    of model JARs for MDT
    """
    _TO_BE_INSTALLED_ROOT_DIRECTORY = "/etc/opt/ericsson/models/toBeInstalled/"

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def _create_model_layout(self, model_jar_location: str):
        """
        Lays out the jars in the supplied directories in the format of:
        /<rpm_name>/<rpm_version>/<jars>

        :param: model_jar_location - location of the model jar
        :return: None
        """
        self.logger.info('Supplied directory: %s', model_jar_location)
        self.logger.info('Starting create model layout...')
        model_type = get_model_type()
        jars = 0

        for jar_file in os.listdir(model_jar_location):
            jars += 1
            command = ['rpm', '-qf', str(model_jar_location) + '/' + jar_file]
            source_rpm_information = execute_subprocess_command(command, True)

            rpm_name, rpm_version = decode_rpm_name(source_rpm_information)
            rpm_dir = pathlib.Path(self._TO_BE_INSTALLED_ROOT_DIRECTORY, rpm_name, rpm_version)

            rpm_dir.mkdir(parents=True, exist_ok=True)
            move(str(model_jar_location) + '/' + jar_file, rpm_dir)

        self.logger.info('Create model layout complete, '
                         '%i jars setup to deploy for model type %s', jars, model_type)

    def generate_layout(self):
        """
        Main object function to: validate input directory & layout model jar contents

        :return: None
        """
        model_jar_location = sys.argv[1]
        validate_input_directories(model_jar_location)
        self._create_model_layout(model_jar_location)


if __name__ == '__main__':
    model_layout_tool = ModelLayoutTool()
    model_layout_tool.generate_layout()
