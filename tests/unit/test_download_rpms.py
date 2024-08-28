"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import pytest

from download_rpms import RpmDownloadTool

TEST_DD_PATH = "tests/resources/test_dd.xml"
TEST_MODEL_PACKAGES = [
    "ERICnodemodelcommonrpm_CX1234567",
    "ERICnodemodelrpm_CX1234567",
    "ERICpostinstallrpm_CX1234567",
    "ERICservicemodelrpm_CX1234567"
]


@pytest.fixture
def fake_success_download_process(fake_process):
    """
    Create successful fake zypper process for test packages
    """
    fake_process.register_subprocess(['zypper', 'in', "--download-only", "-y",
                                      *TEST_MODEL_PACKAGES], returncode=0)


@pytest.fixture
def fake_failure_download_process(fake_process):
    """
    Create unsuccessful fake zypper process for test packages
    """
    fake_process.register_subprocess(['zypper', 'in', "--download-only", "-y",
                                      *TEST_MODEL_PACKAGES], returncode=1)


@pytest.fixture
def test_download_rpm_tool(monkeypatch):
    """
    Create a test download rpm tool with deployment descriptor overridden

    :return: A test rpm download tool
    """
    rpm_download_tool = RpmDownloadTool()
    monkeypatch.setattr(rpm_download_tool, "_DEPLOYMENT_DESCRIPTOR", TEST_DD_PATH)
    return rpm_download_tool


class TestDownloadRPMs:
    """
    Test class for script `modeling_utils.download_rpms`.
    """

    def test_download_model_rpms_success(self, fake_success_download_process,
                                         test_download_rpm_tool):
        test_download_rpm_tool.download_model_rpms()

    def test_download_model_rpms_when_zypper_failure_system_exit(self, fake_failure_download_process,
                                                          test_download_rpm_tool):
        with pytest.raises(SystemExit) as error:
            test_download_rpm_tool.download_model_rpms()
        assert error

    def test_download_model_rpms_when_no_dd_fail(self, monkeypatch):
        rpm_download_tool = RpmDownloadTool()
        monkeypatch.setattr(rpm_download_tool, "_DEPLOYMENT_DESCRIPTOR", "doesnt/exist")
        with pytest.raises(FileNotFoundError) as error:
            rpm_download_tool.download_model_rpms()
        assert error
