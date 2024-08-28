#!/bin/bash
# ********************************************************************
#
# (c) Ericsson LMI 2022 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property
# of Ericsson LMI. The programs may be used and/or copied only with
# the written permission from Ericsson LMI or in accordance with the
# terms and conditions stipulated in the agreement/contract under
# which the program(s) have been supplied.
#
# ********************************************************************

_BASENAME=/usr/bin/basename
_CAT=/usr/bin/cat
_CP=/usr/bin/cp
_CUT=/usr/bin/cut
_ECHO=/usr/bin/echo
_FIND=/usr/bin/find
_LOGGER=/usr/bin/logger
_JAVA=/usr/bin/java
_MKDIR=/usr/bin/mkdir
_RM=/usr/bin/rm
_RPM=/usr/bin/rpm
_RSYSLOG=/sbin/rsyslogd
_ZYPPER=/usr/bin/zypper
SCRIPT_NAME="$(${_BASENAME} "${0}")"

RPM_DIR="/ericsson/customModelRpms"
MODEL_JARS_DIR="/var/opt/ericsson/ERICmodeldeployment/data/install"
CUSTOM_TO_BE_INSTALLED_DIR="/etc/opt/ericsson/ERICmodeldeployment/data/execution/customToBeInstalled"
MDC_CLASSPATH="/opt/ericsson/ERICmodeldeploymentclient/lib/*"
MDC_MAIN_CLASS="com.ericsson.oss.itpf.modeling.model.deployment.client.main.ModelDeploymentClientStart"


# Log at DEBUG level to /var/log/messages only.
#
# Args:
#   message - Message string to log
debug() {
    ${_LOGGER} -t "${SCRIPT_NAME}" -p user.debug "DEBUG: $*"
}

# Log at INFO level to /var/log/messages and console.
#
# Args:
#   message - Message string to log
info() {
    ${_LOGGER} -s -t "${SCRIPT_NAME}" -p user.info "INFO: ${*}"
}

# Log at ERROR level to /var/log/messages and console.
#
# Args:
#   message - Message string to log
error() {
    ${_LOGGER} -s -t "${SCRIPT_NAME}" -p user.error "ERROR: $*"
}

# Print script usage
printUsage() {
    ${_CAT} << EOF
    Script Name:  ${SCRIPT_NAME}
    Description:  The purpose of this script is to deploy custom model RPMs.

    Prerequisite: Model RPMs must exist in '/ericsson/customModelRpms'

    Usage:        <script_name>
EOF
}

enable_rsyslog() {
  ${_RSYSLOG}
}

# Verify that the optional argument supplied to the script is valid.
#
# Args:
#   @ - Arguments supplied to the script
verifyInput() {
    if [[ ${#} -gt 1 ]]; then
         error "Invalid script arguments supplied: '${@}'"
         printUsage
         exit 1
    fi

    input="${1}"
    if [[ ! -z "$input" ]];then
        case "${input}" in
          help)
              printUsage
              exit 0
              ;;
          *)
              error "Invalid script argument supplied: '${input}'"
              printUsage
              exit 1
              ;;
        esac
    fi
}

# Verify that the RPM directory exists and contains RPMs.
verifyRpmDir() {
    if [[ ! -d "${RPM_DIR}" ]]; then
        error "'${RPM_DIR}' directory does not exist."
        printUsage
        exit 1
    fi
    listOfRpms="$(${_FIND} "${RPM_DIR}" -maxdepth 1 -iname '*.rpm')"
    if [ -z "${listOfRpms}" ]; then
        error "'${RPM_DIR}' does not contain RPMs."
        printUsage
        exit 1
    fi
}

# Clean up contents of directory provided.
#
# Args:
#   directoryToCleanUp - directory to clean
cleanUpDirContents() {
    directoryToCleanUp="${1}"
    info "Removing the contents of '${directoryToCleanUp}'."
    ${_RM} -rf ${directoryToCleanUp}/*
    if [[ $? != 0 ]]; then
        error "Unable to remove the contents of '${directoryToCleanUp}'."
    fi
}

# Install RPMs supplied in the RPM directory
installCopiedModelRpms() {
    info "Unpacking model RPMs."

    info "Allowing unsigned model RPMs."
    ${_ZYPPER} install -y --allow-unsigned-rpm ${RPM_DIR}/*.rpm

    if [[ $? != 0 ]]; then
        error "Unable to unpack model RPMs located in: '${RPM_DIR}'"
        exit 1
    fi
}

# Create the directory structure needed for model deployment from the jars installed.
createLayout() {
    listOfJars="$(${_FIND} "${MODEL_JARS_DIR}" -maxdepth 1 -iname '*.jar')"

    if [ -n "${listOfJars}" ]; then
        info "Creating model directory structure for jars in '${MODEL_JARS_DIR}'."
        for jar in ${listOfJars}; do
            rpmFullName="$(${_RPM} -qf "${jar}")"
            debug "Model JAR: '${jar}' is associated with ${rpmFullName}"

            rpmName="$(${_ECHO} "${rpmFullName}"| ${_CUT} -d'-' -f1)"
            if [[ -z "${rpmName}" ]]; then
                error "Unable to retrieve the RPM name of '${jar}'."
                exit 1
            fi

            rpmVersionWithSuffix="$(${_ECHO} "$rpmFullName" | ${_CUT} -d"-" -f2)"
            if [[ "${rpmVersionWithSuffix}" == *".noarch"* ]]; then
                rpmVersion="${rpmVersionWithSuffix%.*}"
            else
                rpmVersion="${rpmVersionWithSuffix}"
            fi

            if [[ -z "${rpmVersion}" ]]; then
                error "Unable to retrieve the RPM version of '${jar}'."
                exit 1
            fi

            debug "Creating directory structure: '${CUSTOM_TO_BE_INSTALLED_DIR}/${rpmName}/${rpmVersion}'."
            ${_MKDIR} -p "${CUSTOM_TO_BE_INSTALLED_DIR}/${rpmName}/${rpmVersion}"
            if [[ $? != 0 ]]; then
                error "Cannot create directory '${CUSTOM_TO_BE_INSTALLED_DIR}/${rpmName}/${rpmVersion}'."
                exit 1
            fi

            debug "Copying '${jar}' to '${CUSTOM_TO_BE_INSTALLED_DIR}/${rpmName}/${rpmVersion}'."
            ${_CP} "${jar}" "${CUSTOM_TO_BE_INSTALLED_DIR}/${rpmName}/${rpmVersion}/"
            if [[ $? != 0 ]]; then
                error "Cannot copy '${jar}' to directory '${CUSTOM_TO_BE_INSTALLED_DIR}/${rpmName}/${rpmVersion}''"
                exit 1
            fi
        done
    else
        error "No model jars found in '${MODEL_JARS_DIR}'."
        exit 1
    fi
}

# Remove the contents of the customToBeInstalled directory and uninstall model RPMs
cleanUp() {
    cleanUpDirContents "${CUSTOM_TO_BE_INSTALLED_DIR}"
    listOfRpms="$(${_FIND} "${RPM_DIR}" -maxdepth 1 -iname '*.rpm' -exec bash -c "${_BASENAME} -s '.rpm' {}" \;)"
    if [ -n "${listOfRpms}" ]; then
        for modelRpm in ${listOfRpms}; do
            ${_ZYPPER} remove -y "${modelRpm}"
        done
    fi
    cleanUpDirContents "${RPM_DIR}"
}

# Run model deployment
runMdt() {
    javaCmdArgs=(-cp "${MDC_CLASSPATH}" ${MDC_MAIN_CLASS} "${CUSTOM_TO_BE_INSTALLED_DIR}")

    info "Starting model deployment with command: '${_JAVA} ${javaCmdArgs[@]}'"
    ${_JAVA} "${javaCmdArgs[@]}"

    if [[ $? != 0 ]]; then
        error "Model deployment did not complete successfully. Please check '/var/log/mdt.log' for more details."
        cleanUp
        exit 1
    else
        info "Model deployment completed successfully."
        cleanUp
    fi
}

enable_rsyslog
verifyInput ${@}
verifyRpmDir
cleanUpDirContents "${CUSTOM_TO_BE_INSTALLED_DIR}"
installCopiedModelRpms
createLayout
runMdt
