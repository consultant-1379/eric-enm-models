#!/usr/bin/env python3
"""
COPYRIGHT Ericsson 2020
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import xml.etree.ElementTree as ET
from subprocess import CalledProcessError
from typing import List

from logger_utils import get_logger
from command_executor import execute_subprocess_command


class RpmDownloadTool:
    """
    This class is responsible for downloading the RPMs found in the deployment descriptor
    into the zypper cache
    """
    _DEPLOYMENT_DESCRIPTOR = "/ericsson/deploymentDescriptions/" \
                            "extraLarge/extraLarge__production_IPv4_dd.xml"

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def __download_rpms(self, rpms: List):
        """
        Download supplied model RPMs

        :param   rpms - A list of model RPMs to download
        :return: None
        """
        download_command = ["zypper", "in", "--download-only", "-y"]
        download_command.extend(rpms)

        try:
            execute_subprocess_command(download_command)
            self.logger.info("Model RPMs downloaded successfully")
        except CalledProcessError as zypper_error:
            self.logger.error(f"Model RPMs download failed: {zypper_error.stderr}")
            raise SystemExit(2) from zypper_error

    @staticmethod
    def __get_all_model_rpms(root_element: ET.Element) -> List:
        """
        Find all model RPMs.

        :param  root_element - root element of the deployment descriptor
        :return: A list of model RPMs found in the deployment descriptor
        """
        rpms = []

        for entry in root_element.findall('.//'):
            if 'model-package' in str(entry):
                for model_entry in entry:
                    rpms.append(model_entry.text)

        return rpms

    @staticmethod
    def __get_root_element(xml_file: str) -> ET.Element:
        """
        Get root element of XML file
        :param xml: Path to an XML file
        :return: root of XML tree
        """
        tree = ET.parse(xml_file)
        return tree.getroot()

    def download_model_rpms(self):
        """
        Carries out the entire process to download RPMs

        :return: None
        """
        self.logger.info('Starting download of model RPMs...')
        root_element = self.__get_root_element(self._DEPLOYMENT_DESCRIPTOR)
        model_rpms_to_download = self.__get_all_model_rpms(root_element)
        self.logger.debug('RPMs being downloaded: %s', model_rpms_to_download)
        self.logger.info('RPMs being downloaded count: %s', len(model_rpms_to_download))

        self.__download_rpms(model_rpms_to_download)
        self.logger.info('Finished download of model RPMs...')


if __name__ == '__main__':
    rpm_download_tool = RpmDownloadTool()
    rpm_download_tool.download_model_rpms()
