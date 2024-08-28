#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2021
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import os
import json
from abc import abstractmethod
from typing import List

from command_executor import execute_subprocess_command

"""
Python file containing the classes which hold the logic
to work out what models should be deployed based on input
"""


class Strategy:
    """
    Strategy interface declaring operations common to all implementing classes
    that are to be used to determine what models are to be deployed
    """

    @abstractmethod
    def get_models_for_deployment(self) -> List:
        """
        Function to get the models for deployment
        """


class FilterStrategy(Strategy):
    """
    Filter Strategy interface declaring operations common to all install
    strategies that identify models to deploy by parsing a repo cache
    based on a model category
    """

    _ENM_ISO_REPO_PATH = '/var/cache/zypp/packages/enm_iso_repo/'

    @abstractmethod
    def get_models_for_deployment(self) -> List:
        """
        Function to get NRMs for deployment
        """

    def get_rpm_name(self, rpm_file, model_directory_type) -> str:
        """
        Get the model RPM name from the models installed on the system

        :param rpm_file: the full RPM file on the system, including the version
        :param model_directory_type: the type of models to be installed - install or post_install
        :return: the name of the RPM file
        """
        rpm_check_install_path_command = ['rpm', '-qpl', self._ENM_ISO_REPO_PATH + rpm_file]
        rpm_install_path = str(execute_subprocess_command(rpm_check_install_path_command, True))
        expected_install_dir = '/' + model_directory_type + '/'
        if expected_install_dir in rpm_install_path:
            return rpm_file.split('-', 1)[0]
        return None


class NrmsForDeployment(FilterStrategy):
    """
    Class containing logic for determining the NRMs to deploy
    """

    def __init__(self):
        self.model_directory_type = "install"

    def get_models_for_deployment(self) -> List:
        """
        Function to get NRMs for deployment

        :return: a list of service model RPMs to install
        """
        rpms_to_install = []
        for _, _, files in os.walk(self._ENM_ISO_REPO_PATH):
            for rpm_file in files:
                rpm_name = super().get_rpm_name(rpm_file, self.model_directory_type)
                if rpm_name is not None:
                    if 'nodemodel' in str(rpm_name):
                        rpms_to_install.append(rpm_name)

        return rpms_to_install


class ServiceModelsForDeployment(FilterStrategy):
    """
    Class containing logic for determining the service models to deploy
    """

    def __init__(self):
        self.model_directory_type = "install"

    def get_models_for_deployment(self) -> List:
        """
        Function to get service models for deployment

        :return: a list of service model RPMs to install
        """
        rpms_to_install = []
        for _, _, files in os.walk(self._ENM_ISO_REPO_PATH):
            for rpm_file in files:
                rpm_name = super().get_rpm_name(rpm_file, self.model_directory_type)
                if rpm_name is not None:
                    if 'nodemodel' not in str(rpm_name):
                        rpms_to_install.append(rpm_name)

        return rpms_to_install


class PostInstallModelsForDeployment(FilterStrategy):
    """
    Class containing logic for determining the post install models to deploy
    """

    def __init__(self):
        self.model_directory_type = "post_install"

    def get_models_for_deployment(self) -> List:
        """
        Function to get post-install models for deployment

        :return: a list of service model RPMs to install
        """
        rpms_to_install = []
        for _, _, files in os.walk(self._ENM_ISO_REPO_PATH):
            for rpm_file in files:
                rpm_name = super().get_rpm_name(rpm_file, self.model_directory_type)
                if rpm_name is not None:
                    rpms_to_install.append(rpm_name)

        return rpms_to_install


class ExplicitModelsForDeployment(Strategy):
    """
    Class containing logic to explicitly deploy requested models
    """
    def __init__(self, rpms_to_install: List):
        self.rpms = rpms_to_install

    def get_models_for_deployment(self) -> List:
        """
        Function to get explicit models for deployment

        :return: a list of model RPMs to install
        """
        return self.rpms


class ModelInstallerStrategy:
    """
    Class that is used to get models that are to be deployed
    """

    @staticmethod
    def get_models_to_deploy(rpm_file_path) -> List:
        """
        Function to get the models to deploy

        :param rpm_file_path: the category of models to deploy
        :return: a list of model RPMs to install
        """
        models_deployment_strategy = ModelInstallerStrategy.__get_deployment_strategy(rpm_file_path)
        return models_deployment_strategy.get_models_for_deployment()

    @staticmethod
    def __get_model_category(rpm_file_path):
        with open(rpm_file_path, 'r') as rpm_file:
            data = json.load(rpm_file)
            try:
                return data['deploy']['model-category']
            except KeyError:
                return None

    @staticmethod
    def __get_model_rpms_to_install(rpm_file_path) -> List:
        with open(rpm_file_path, 'r') as rpm_file:
            data = json.load(rpm_file)
            try:
                return data['deploy']['rpms']
            except KeyError:
                return []

    @staticmethod
    def __get_deployment_strategy(rpm_file_path) -> Strategy:
        """
        Function to get the Strategy to use to deploy models

        :param rpm_file_path: the deploy rpm file
        :return: Strategy to deploy models
        """
        models_category = ModelInstallerStrategy.__get_model_category(rpm_file_path)

        if models_category is not None:
            if models_category == 'service_models':
                return ServiceModelsForDeployment()
            if models_category == 'nrm_models':
                return NrmsForDeployment()
            if models_category == 'post_install':
                return PostInstallModelsForDeployment()

            raise ValueError(f"Strategy could not be determined by model category"
                             f" {models_category}")

        model_rpms = ModelInstallerStrategy.__get_model_rpms_to_install(rpm_file_path)
        if len(model_rpms) != 0:
            return ExplicitModelsForDeployment(model_rpms)

        raise ValueError(f"Could not determine model RPMs to install via {rpm_file_path}")
