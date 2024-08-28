"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import pytest

from model_installer_strategy import FilterStrategy, ModelInstallerStrategy

RPM_CACHE = "tests/resources/zypper_cache/"
DEPLOY_FILES_DIR = "tests/resources/deploy_files/"

NRM_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "node_model.json"
POST_INSTALL_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "post_install.json"
SERVICE_MODELS_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "service_model.json"
EXPLICIT_MODELS_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "explicit.json"
INVALID_CATEGORY_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "incorrect_category.json"
EMPTY_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "empty.json"
NOT_PARSABLE_DEPLOY_FILE_PATH = DEPLOY_FILES_DIR + "not_parseable.json"

NRM_RPM_PATH = RPM_CACHE + "ERICnodemodelrpm_CX1234567-1.0.1.rpm"
NRM_COMMON_RPM_PATH = RPM_CACHE + "ERICnodemodelcommonrpm_CX1234567-1.0.1.rpm"
POST_INSTALL_RPM_PATH = RPM_CACHE + "ERICpostinstallrpm_CX1234567-1.0.1.rpm"
SERVICE_MODEL_RPM_PATH = RPM_CACHE + "ERICservicemodelrpm_CX1234567-1.0.1.rpm"

SUCCESS_TEST_PARAMS = [
    (NRM_DEPLOY_FILE_PATH, ["ERICnodemodelcommonrpm_CX1234567",
                            "ERICnodemodelrpm_CX1234567"]),
    (POST_INSTALL_DEPLOY_FILE_PATH, ["ERICpostinstallrpm_CX1234567"]),
    (SERVICE_MODELS_DEPLOY_FILE_PATH, ["ERICservicemodelrpm_CX1234567"]),
    (EXPLICIT_MODELS_DEPLOY_FILE_PATH, ["ERICnodemodelcommonrpm_CX1234567",
                                        "ERICservicemodelrpm_CX1234567"])
]


@pytest.fixture
def setup_zypper_cache(fake_process, monkeypatch):
    """
    Creates fake processes for each of the test RPMs and overrides _ENM_ISO_REPO_PATH for testing
    """
    install = "/install/"
    post_install = "/post_install/"
    rpm_path_to_output = {NRM_RPM_PATH: install,
                          NRM_COMMON_RPM_PATH: install,
                          POST_INSTALL_RPM_PATH: post_install,
                          SERVICE_MODEL_RPM_PATH: install}

    for rpm_path, output in rpm_path_to_output.items():
        fake_process.register_subprocess(['rpm', '-qpl', rpm_path], stdout=output)
        fake_process.keep_last_process(True)

    monkeypatch.setattr(FilterStrategy, "_ENM_ISO_REPO_PATH", RPM_CACHE)


class TestModelInstallerStrategy:
    """
    Test class for class model_installer_strategy.ModelInstallStrategy
    """

    @pytest.mark.parametrize("deploy_file_path,expected_output", SUCCESS_TEST_PARAMS)
    def test_get_models_to_deploy_success(self, deploy_file_path, expected_output,
                                          setup_zypper_cache):
        actual = ModelInstallerStrategy.get_models_to_deploy(deploy_file_path)
        assert actual == expected_output

    def test_get_models_to_deploy_given_invalid_model_category_raise_value_error(self):
        with pytest.raises(ValueError) as error:
            ModelInstallerStrategy.get_models_to_deploy(INVALID_CATEGORY_DEPLOY_FILE_PATH)
        assert "Strategy could not be determined by model category incorrect" == error.value.args[0]

    def test_get_models_to_deploy_given_empty_deploy_file_raise_value_error(self):
        with pytest.raises(ValueError) as error:
            ModelInstallerStrategy.get_models_to_deploy(EMPTY_DEPLOY_FILE_PATH)
        expected_error = "Could not determine model RPMs to install via " + EMPTY_DEPLOY_FILE_PATH
        assert expected_error == error.value.args[0]

    def test_get_models_to_deploy_given_not_parsable_deploy_file_raise_error(self):
        with pytest.raises(Exception) as error:
            ModelInstallerStrategy.get_models_to_deploy(NOT_PARSABLE_DEPLOY_FILE_PATH)
        assert error

    def test_get_models_to_deploy_when_no_deploy_file_raise_error(self):
        with pytest.raises(Exception) as error:
            ModelInstallerStrategy.get_models_to_deploy("doesnt_exist")
        assert error
