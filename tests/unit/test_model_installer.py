"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import pytest

from model_installer import ModelInstaller

INSTALL_DIRECTORY = "rpms"
TEST_MODEL_PACKAGES = [
    "ERICnodemodelcommonrpm_CX1234567",
    "ERICnodemodelrpm_CX1234567",
    "ERICpostinstallrpm_CX1234567",
    "ERICservicemodelrpm_CX1234567"
]


@pytest.fixture
def setup_fake_success_zypper_process(fake_process):
    """
    Create successful fake zypper process for test packages
    """
    fake_process.register_subprocess(['zypper', 'in', "-y", *TEST_MODEL_PACKAGES], returncode=0)


@pytest.fixture
def setup_fake_failure_zypper_process(fake_process):
    """
    Create unsuccessful fake zypper process for test packages
    """
    fake_process.register_subprocess(['zypper', 'in', "-y", *TEST_MODEL_PACKAGES], returncode=1)


class TestModelInstaller:
    """
    Test class for script `modeling_utils.model_installer`.
    """

    def test_install_model_rpm_success(self, setup_fake_success_zypper_process):

        model_installer = ModelInstaller("deploy_file")
        model_installer._install_model_rpms(TEST_MODEL_PACKAGES)

    def test_install_model_rpm_when_install_fail_system_exit(self,
                                                             setup_fake_failure_zypper_process):
        model_installer = ModelInstaller("deploy_file")
        with pytest.raises(SystemExit) as error:
            model_installer._install_model_rpms(TEST_MODEL_PACKAGES)
        assert error
