"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
import pathlib
from typing import Dict

import pytest

from create_model_layout import validate_input_directories, get_model_type, ModelLayoutTool

JAR_PATH = "valid/path/install"
TEST_INVALID_PATH = "invalid/path"
TEST_JAR_FILE_TEMPLATE = "models-{}.jar"
TEST_RPM_NAME_ONE = "ERICrpm_CXP1234567-1.0.1"
TEST_RPM_NAME_TWO = "ERICotherrpm_CXP1234567-1.0.2"


@pytest.fixture
def setup_invalid_directory(tmp_path):
    """
    Setup an invalid model jar directory that does not end in "install" or "post_install"

    :return: The created invalid directory path as a string
    """
    invalid_directory = tmp_path.joinpath(TEST_INVALID_PATH)
    invalid_directory.mkdir(parents=True)
    return str(invalid_directory)


@pytest.fixture
def setup_jars(monkeypatch, tmp_path, fake_process, rpm_name_to_jars: Dict):
    """
    Setup input dir with mock file jars, overwrite sys.argv to that directory.
    """
    jar_directory = tmp_path.joinpath(JAR_PATH)
    cli_args = ["first_param_is_discarded", str(jar_directory)]
    monkeypatch.setattr('sys.argv', cli_args)

    jar_directory.mkdir(parents=True)
    jar_number = 0
    for rpm, num_of_jars in rpm_name_to_jars.items():
        for jar in range(0, num_of_jars):
            jar_file = jar_directory.joinpath(TEST_JAR_FILE_TEMPLATE.format(jar_number))
            jar_file.touch()
            fake_process.register_subprocess(['rpm', '-qf', str(jar_file)],
                                             stdout=bytes(rpm, encoding='utf8'))
            jar_number += 1


@pytest.fixture
def set_models_type_env(monkeypatch):
    """
    Set 'MODELS_TYPE' env
    """
    monkeypatch.setenv("MODELS_TYPE", "value")


@pytest.fixture
def test_layout_tool(tmp_path, setup_jars):
    """
    Create test instance of ModelLayoutTool with install directory overridden to tmp location

    :return: instance of ModelLayoutTool
    """
    test_model_layout_tool = ModelLayoutTool()
    test_model_layout_tool._TO_BE_INSTALLED_ROOT_DIRECTORY = tmp_path.joinpath("test_install_dir")

    return test_model_layout_tool


class TestCreateModelLayout:

    def test_create_layout_no_directory_supplied_failure(self):
        with pytest.raises(ValueError) as error:
            validate_input_directories("")
        assert "No model directory supplied" == error.value.args[0]

    def test_create_layout_invalid_directory_failure(self, setup_invalid_directory):
        invalid_directory = setup_invalid_directory
        with pytest.raises(ValueError) as error:
            validate_input_directories(invalid_directory)
        assert "Model directories must end with 'install' or 'post_install'." \
               f" {invalid_directory} supplied" == error.value.args[0]

    def test_create_layout_directory_does_not_exist_failure(self):
        with pytest.raises(ValueError) as error:
            validate_input_directories('/does/not/exist')
        assert 'Supplied directory "/does/not/exist" does not exist' == error.value.args[0]

    def test_create_layout_models_type_not_set_failure(self):
        with pytest.raises(EnvironmentError) as error:
            get_model_type()
        assert error.value.args[0] == 'MODELS_TYPE environment variable not found'

    def test_create_layout_models_type_set_success(self, set_models_type_env):
        get_model_type()

    @pytest.mark.parametrize('rpm_name_to_jars', [{TEST_RPM_NAME_ONE: 1}])
    def test_create_layout_one_rpm_one_jar_success(self, test_layout_tool, set_models_type_env):
        install_dir = test_layout_tool._TO_BE_INSTALLED_ROOT_DIRECTORY
        installed_jar_file = pathlib.Path(install_dir).joinpath("ERICrpm_CXP1234567")\
            .joinpath("1.0.1").joinpath("models-0.jar")

        assert not install_dir.exists()
        test_layout_tool.generate_layout()

        assert installed_jar_file.exists()

    @pytest.mark.parametrize('rpm_name_to_jars', [{TEST_RPM_NAME_ONE: 2, TEST_RPM_NAME_TWO: 1}])
    def test_create_layout_two_rpm_three_jars_success(self, test_layout_tool, set_models_type_env):
        install_dir = test_layout_tool._TO_BE_INSTALLED_ROOT_DIRECTORY
        rpm_one_dir = install_dir.joinpath("ERICrpm_CXP1234567").joinpath("1.0.1")
        rpm_one_jar_one = rpm_one_dir.joinpath("models-0.jar")
        rpm_one_jar_two = rpm_one_dir.joinpath("models-1.jar")
        rpm_two_jar_one = install_dir.joinpath("ERICotherrpm_CXP1234567")\
            .joinpath("1.0.2").joinpath("models-2.jar")

        assert not install_dir.exists()
        test_layout_tool.generate_layout()

        assert rpm_one_jar_one.exists()
        assert rpm_one_jar_two.exists()
        assert rpm_two_jar_one.exists()
