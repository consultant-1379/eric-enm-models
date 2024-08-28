#!/usr/bin/env groovy

/*------------------------------------------------------------------------------
 *******************************************************************************
 * COPYRIGHT Ericsson 2020
 *
 * The copyright to the computer program(s) herein is the property of
 * Ericsson Inc. The programs may be used and/or copied only with written
 * permission from Ericsson Inc. or in accordance with the terms and
 * conditions stipulated in the agreement/contract under which the
 * program(s) have been supplied. 
 *******************************************************************************
 *----------------------------------------------------------------------------
 *
 * IMPORTANT:
 *
 * In order to make this pipeline work, the following configuration on Jenkins is required:
 *  - slave with a specific label (see pipeline.agent.label below)
 *  - credentials plugin should be installed and have the secrets with the following names:
 *    + lciadm100credentials (token to access Artifactory)
 */

def GIT_COMMITTER_NAME = 'enmadm100'
def GIT_COMMITTER_EMAIL = 'enmadm100@ericsson.com'
def defaultBobImage = 'armdocker.rnd.ericsson.se/sandbox/adp-staging/adp-cicd/bob.2.0:1.7.0-95'
def bob = ''
def failedStage = ''

pipeline {

    agent {
        label 'Cloud-Native'
    }

    parameters {
        string(name: 'ISO_VERSION', description: 'The ENM ISO version (e.g. 1.65.77)')
        string(name: 'SPRINT_TAG', description: 'Tag for GIT tagging the repository after build')
        string(name: 'PRODUCT_SET', description: 'cENM product set (e.g. 21.1.13-1)')
    }

    environment {
        RELEASE = "true"
        GERRIT_HTTP_CREDENTIALS_FUser = credentials('FUser_gerrit_http_username_password')
    }

    stages {

        stage('Inject Credential Files') {
            steps {
                withCredentials([file(credentialsId: 'lciadm100-docker-auth', variable: 'dockerConfig')]) {
                    sh "install -m 600 ${dockerConfig} ${HOME}/.docker/config.json"
                }
            }
        }

        stage('Init') {
            steps {
                script {
                    def bobCmd = load 'jenkins/BobCommand.groovy'
                    bob = bobCmd
                            .bobImage(defaultBobImage)
                            .needDockerSocket(true)
                            .envVars([
                                'ISO_VERSION'        : '${ISO_VERSION}',
                                'AUTHOR_NAME'        : "\${BUILD_USER:-${GIT_COMMITTER_NAME}}",
                                'AUTHOR_EMAIL'       : "\${BUILD_USER_EMAIL:-${GIT_COMMITTER_EMAIL}}",
                                'GIT_COMMITTER_NAME' : "${GIT_COMMITTER_NAME}",
                                'GIT_COMMITTER_EMAIL': "${GIT_COMMITTER_EMAIL}",
                                'RELEASE'            : "${RELEASE}"])
                            .toString()
                }
            }
        }

        stage('Clean') {
            steps {
                sh "${bob} clean"
            }
        }

        stage('Checkout Cloud-Native Service Git Repository') {
            steps {
                git branch: 'master',
                        url: '${GERRIT_MIRROR}/OSS/com.ericsson.oss.cloudcommon.models/eric-enm-models'
                sh '''
                    git remote set-url origin --push https://${GERRIT_HTTP_CREDENTIALS_FUser}@${GERRIT_CENTRAL_HTTP_E2E}/OSS/com.ericsson.oss.cloudcommon.models/eric-enm-models
                '''
            }
        }

        stage('Swap versions in Dockerfile file'){
            steps{
                echo sh(script: 'env', returnStdout:true)
                step ([$class: 'CopyArtifact', projectName: 'sync-build-trigger', filter: "*"]);
                sh "${bob} swap-latest-versions-with-numbers"
                sh '''
                    if git status | grep 'Dockerfile' > /dev/null; then
                        git commit -m "NO JIRA - Updating Dockerfile with base image version"
                    else
                        echo `date` > timestamp
                        git add timestamp
                        git commit -m "NO JIRA - Time Stamp "
                    fi
                    git push origin HEAD:master
                '''
            }
        }

        stage('Build Models Images') {
            steps {
                sh "${bob} print-docker-info"
                sh "${bob} generate-new-version build-image-with-all-tags"
            }

            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                        sh "${bob} print-docker-info"
                        sh "${bob} remove-image-with-all-tags"
                    }
                }
            }
        }

        stage('Retrieve Image Version') {
            steps {
                script {
                    env.IMAGE_TAG = sh(script: "cat .bob/var.version", returnStdout:true).trim()
                    echo "${IMAGE_TAG}"
                }
            }

            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                        sh "${bob} remove-image-with-all-tags"
                    }
                }
            }
        }

        stage('Generate ADP Parameters') {
            steps {
                sh "${bob} generate-output-parameters"
                archiveArtifacts 'artifact.properties'
            }
            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                    }
                }
            }
        }

        stage('Publish Models Images to Artifactory') {
            steps {
                sh "${bob} push-image-with-all-tags"
            }

            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                        sh "${bob} remove-image-with-all-tags"
                    }
                }

                always {
                    sh "${bob} remove-image-with-all-tags"
                }
            }
        }

        stage('Tag Cloud-Native Service Git Repository') {
            steps {
                wrap([$class: 'BuildUser']) {
                    script {
                        sh "${bob} create-git-tag"
                        sh """
                            tag_id=\$(cat .bob/var.version)
                            git push origin \${tag_id}
                        """
                    }
                }
            }

            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                    }
                }

                always {
                    script {
                        sh "${bob} remove-git-tag"
                    }
                }
            }
        }
    }
    post {
         success {
            script {
                sh '''
                    set +x
                    git tag --annotate --message "Tagging latest in sprint" --force $SPRINT_TAG HEAD
                    git push --force origin $SPRINT_TAG
                    git tag --annotate --message "Tagging latest in sprint with ISO version" --force ${SPRINT_TAG}_iso_${ISO_VERSION} HEAD
                    git push --force origin ${SPRINT_TAG}_iso_${ISO_VERSION}
                    git tag --annotate --message "Tagging latest in sprint with Product Set version" --force ps_${PRODUCT_SET} HEAD
                    git push --force origin ps_${PRODUCT_SET}
                '''
            }
        }
        failure {
            mail to: 'PDLTORSERV@pdl.internal.ericsson.com',
                 from: "enmadm100@lmera.ericsson.se",
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "Failure on ${env.BUILD_URL}"
        }
    }
}
