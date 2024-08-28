"""
COPYRIGHT Ericsson 2022
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.
"""
from unittest import mock
from os import path

import pytest

from trigger_mdt import MdtTool

TEST_SERVICE_FILE_PATH = "temp/test_service_file_path"
MDC_CLASSPATH = 'opt/ericsson/ERICmodeldeploymentclient/lib/*'
MDC_MAINCLASS = 'com.ericsson.oss.itpf.modeling.model.deployment.client.main.ModelDeploymentClientStart'
MODELLING_MOUNT_POINT = 'etc/opt/ericsson/ERICmodeldeployment/'
MODEL_DEPLOYMENT_SERVICE_FILE = MODELLING_MOUNT_POINT + 'data/ModelDeploymentService'
MDT_MODELS_DIR = MODELLING_MOUNT_POINT + "data/execution/toBeInstalled/model_type/timestamp"
MDT_MODELS_DIR2 = MODELLING_MOUNT_POINT + "data/execution/toBeInstalled/model_type/timestamp2"
TEST_TO_BE_INSTALLED_DIR = "test_to_be_installed/test"
TO_BE_INSTALLED_RPM_1_DIR = TEST_TO_BE_INSTALLED_DIR + "/ERICnodemodelrpm_CX1234567/1.0.1"
TO_BE_INSTALLED_RPM_2_DIR = TEST_TO_BE_INSTALLED_DIR + "/ERICnodemodelcommonrpm_CX1234567/1.0.1"
TO_BE_INSTALLED_JAR = "models.jar"


@pytest.fixture
def override_java_command(fake_process, tmp_path):
    """
    Creates a fake java subprocess that exits successfully
    """
    fake_process.register_subprocess(['java', '-cp', str(tmp_path.joinpath(MDC_CLASSPATH)),
                                      MDC_MAINCLASS, "test"], returncode=0)


@pytest.fixture
def test_service_file_path(tmp_path):
    """
    Generates test mdt RMI stub file path

    :return: path of stub file
    """
    return tmp_path.joinpath(TEST_SERVICE_FILE_PATH)


@pytest.fixture
def test_to_be_installed_dir(tmp_path):
    """
    Generates a test to be installed directory path

    :return: a test to be installed directory path
    """
    return tmp_path.joinpath(TEST_TO_BE_INSTALLED_DIR)


@pytest.fixture
def test_mdt_models_dir(tmp_path):
    """
    Generates and returns a test mdt models mount directory path

    :return: test mdt models directory path
    """
    return tmp_path.joinpath(MDT_MODELS_DIR)


@pytest.fixture
def test_mdt_models_dir2(tmp_path):
    """
    Generates and returns a second test mdt models mount directory path, with a different timestamp

    :return: test mdt models directory path
    """
    return tmp_path.joinpath(MDT_MODELS_DIR2)


@pytest.fixture
def setup_test_to_be_installed_directory(tmp_path, test_to_be_installed_dir):
    """
    Creates a test to be installed directory with 2 rpms / 2 jars
    """
    test_to_be_installed_dir.mkdir(parents=True)
    rpm1_dir = test_to_be_installed_dir.joinpath(TO_BE_INSTALLED_RPM_1_DIR)
    rpm2_dir = test_to_be_installed_dir.joinpath(TO_BE_INSTALLED_RPM_2_DIR)

    rpm1_dir.mkdir(parents=True)
    rpm2_dir.mkdir(parents=True)

    jar1 = rpm1_dir.joinpath(TO_BE_INSTALLED_JAR)
    jar2 = rpm2_dir.joinpath(TO_BE_INSTALLED_JAR)

    jar1.touch()
    jar2.touch()


@pytest.fixture
def test_mdt_tool(monkeypatch, tmp_path):
    """
    Creates an MdtTool instance with class constants overridden for testing

    :return: An MdtTool instance
    """
    mdt_tool = MdtTool()
    monkeypatch.setattr(mdt_tool, "_MDC_CLASSPATH", str(tmp_path.joinpath(MDC_CLASSPATH)))
    monkeypatch.setattr(mdt_tool, "_MODELLING_MOUNT_POINT", str(tmp_path.joinpath(MODELLING_MOUNT_POINT)))
    monkeypatch.setattr(mdt_tool, "_MODEL_DEPLOYMENT_SERVICE_FILE",
                        str(tmp_path.joinpath(MODEL_DEPLOYMENT_SERVICE_FILE)))
    monkeypatch.setattr(mdt_tool, "_SLEEP_INTERVAL", 0)
    return mdt_tool


class TestTriggerMdt:
    """
    Test class for script trigger_mdt
    """

    def test_copy_model_jars_to_model_mount_success(self, test_to_be_installed_dir,
                                                    setup_test_to_be_installed_directory, test_mdt_models_dir,
                                                    test_mdt_tool):
        assert not path.exists(test_mdt_models_dir)
        jar1 = test_mdt_models_dir.joinpath(TO_BE_INSTALLED_RPM_1_DIR).joinpath(TO_BE_INSTALLED_JAR)
        jar2 = test_mdt_models_dir.joinpath(TO_BE_INSTALLED_RPM_2_DIR).joinpath(TO_BE_INSTALLED_JAR)

        test_mdt_tool._copy_model_jars_to_mdt_mount(test_to_be_installed_dir, test_mdt_models_dir)

        assert path.exists(test_mdt_models_dir)
        assert path.exists(jar1)
        assert path.exists(jar2)

    def test_copy_model_jars_to_mdt_mount_when_oserror_then_system_exit(self, test_to_be_installed_dir,
                                                                        test_mdt_models_dir, test_mdt_tool):
        with mock.patch('shutil.copytree', side_effect=OSError("OSError: Copy Failed")):
            with pytest.raises(SystemExit) as exit_after_copy_error:
                test_mdt_tool._copy_model_jars_to_mdt_mount(test_to_be_installed_dir, test_mdt_models_dir)
            assert exit_after_copy_error

    def test_copy_twice_no_errors_cleanup_removes_all_timestamp_dirs(self, test_to_be_installed_dir,
                                                                     setup_test_to_be_installed_directory,
                                                                     test_mdt_models_dir, test_mdt_models_dir2,
                                                                     test_mdt_tool):
        test_mdt_tool._copy_model_jars_to_mdt_mount(test_to_be_installed_dir, test_mdt_models_dir)
        test_mdt_tool._copy_model_jars_to_mdt_mount(test_to_be_installed_dir, test_mdt_models_dir2)

        assert path.exists(test_mdt_models_dir)
        assert path.exists(test_mdt_models_dir2)

        test_mdt_tool._clean_up_old_model_jars(path.dirname(test_mdt_models_dir))

        assert not path.exists(test_mdt_models_dir)
        assert not path.exists(test_mdt_models_dir)
        assert not path.exists(path.dirname(test_mdt_models_dir))

    def test_wait_for_model_deployment_service_file_success(self, test_service_file_path, test_mdt_tool):
        test_service_file_path.mkdir(parents=True)
        test_mdt_tool._wait_for_model_deployment_service_file(test_service_file_path)

    def test_invoke_mdt_via_model_deployment_client_success(self, override_java_command, test_mdt_tool):
        with mock.patch("time.sleep", return_value=None):
            test_mdt_tool._invoke_mdt_via_model_deployment_client("test")

    def test_clean_up_old_model_jars_success(self, tmp_path, test_mdt_tool, test_to_be_installed_dir,
                                             setup_test_to_be_installed_directory):
        assert path.exists(test_to_be_installed_dir)
        test_mdt_tool._clean_up_old_model_jars(test_to_be_installed_dir)
        assert not path.exists(test_to_be_installed_dir)

    def test_clean_up_old_model_jars_when_error_then_system_exit(self, tmp_path, test_mdt_tool,
                                                            test_to_be_installed_dir,
                                                            setup_test_to_be_installed_directory):
        with mock.patch('shutil.rmtree', side_effect=OSError("OSError")):
            with pytest.raises(SystemExit) as error:
                test_mdt_tool._clean_up_old_model_jars(test_to_be_installed_dir)
            assert error
