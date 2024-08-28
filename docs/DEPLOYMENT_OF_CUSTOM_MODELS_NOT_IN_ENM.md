# Create and Deploy Custom Models not existing within ENM

[TOC]

This document is a guide to aid a user in creating and deploying a custom model not existing within ENM in a Kubernetes environment.

## Core Model Image

The core model image provides the required utilities and instructions to install models that are not part of the
standard ENM set. The core image will be used to create custom model image and deploy models during container run time.

This image is provided/tagged as *armdocker.rnd.ericsson.se/proj-enm/eric-enm-models-core-image:<x.y.z-b>*
Versions for this image follow the x.y.z-b format and the latest can be found on [gerrit](https://gerrit-gamma.gic.ericsson.se/gitweb?p=OSS%2Fcom.ericsson.oss.cloudcommon.models%2Feric-enm-models.git;a=summary).

**Restriction**: This image can only install models of the "install" model category. "post-install" is not supported.

## Create Custom Model Image From Core

To create a custom model image consisting of the models that are not part of existing ENM, the respective RPMs
should be placed in the image_content folder in the repository.

#### Sample Repository Structure

```
|-- Dockerfile
|-- image_content
|   `-- model_1_rpm.rpm
|   `-- model_2_rpm.rpm
```

#### Sample Dockerfile

```
ARG ERIC_ENM_MODELS_CORE_IMAGE_NAME=eric-enm-models-core-image
ARG ERIC_ENM_MODELS_CORE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-enm
ARG ERIC_ENM_MODELS_CORE_IMAGE_TAG=x.y.z-b

FROM ${ERIC_ENM_MODELS_CORE_IMAGE_REPO}/${ERIC_ENM_MODELS_CORE_IMAGE_NAME}:${ERIC_ENM_MODELS_CORE_IMAGE_TAG}

COPY image_content/*.rpm /ericsson/customModelRpms/
```

**Note**: the naming conventions for the ARGs in the dockerfile are mandatory as they are used
to automatically update the version of the core image in certain pipelines.

#### Sample Image Build Command

```
docker image build . --tag armdocker.rnd.ericsson.se/proj-enm/my-custom-model-not-in-enm-image:x.y.z-b
```

\
This command will trigger a build following the flow of:

* Pulling the parent core model image
* [COPY](https://docs.docker.com/engine/reference/builder/#copy) the RPMs from image_content to /ericsson/customModelRpms.
* Inheriting the [ENTRYPOINT](https://docs.docker.com/engine/reference/builder/#entrypoint) instruction of the parent to be executed at container startup

\
The above sample configuration will create a custom model delivery image
that deploys the RPMs present in the image_content folder.

## Deploying Custom Model Images in ENM

To install (or upgrade) models on a cENM system, create a **Kubernetes Job** or chart **pre-install/pre-upgrade hook**

Model delivery in a Kubernetes environment should be executed using [Kubernetes Job objects](
https://kubernetes.io/docs/concepts/workloads/controllers/job/).
Additionally the Job should be deployed as a [Helm Hook](https://helm.sh/docs/topics/charts_hooks/).

To install or upgrade custom models on a cENM system, a Helm Job template must be included in your integration charts.
The template must refer to the custom model image that was built in the previous section.

Before writing the Job template, familiarity with the following Kubernetes and Helm constructs is recommended:

#### Helm flow control

[Helm Flow Control](https://helm.sh/docs/chart_template_guide/control_structures/) should be used to allow for the inclusion/exclusion of
optional sections of the job depending on a chosen parameter included in the chart values file.

#### Sample Values Configuration

The values file of your chart needs to be updated to describe:

* The custom model image name and tag. Should be appended to the existing 'images' subsection of the chart.

See example below:
```
images:
  fm-sdk-custom-models:
    name: fm-sdk-custom-models
    tag: x.y.z-b

fm-sdk-custom-models-job:
  name: fm-sdk-custom-models
  restartPolicy: OnFailure
```

#### Sample Template
The provided template should be modified to reflect the updated values file.
For the sample values file update above:

* ```<custom-model-job-values>``` should be replaced with ```fm-sdk-custom-models-job```.
* ```<custom-model-image>``` should be replaced with ```fm-sdk-custom-models```.


```
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ index .Values "<custom-model-job-values>" "name" }}-job
  labels:
    chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
    release: "{{ .Release.Name }}"
    heritage: "{{ .Release.Service }}"
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  backoffLimit: 8
  template:
    metadata:
      name: {{ index .Values "<custom-model-job-values>" "name" }}-job
      labels:
        chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
        release: "{{ .Release.Name }}"
        heritage: "{{ .Release.Service }}"
    spec:
      restartPolicy: {{ index .Values "<custom-model-job-values>" "restartPolicy" }}
{{- if include "<your-chart>.pullSecrets" . }}
      imagePullSecrets:
        - name: {{ template "<your-chart>.pullSecrets" . }}
{{- end }}
{{- if .Values.images.waitInitContainer.enabled }}
      initContainers:
      - name: {{ index .Values "<custom-model-job-values>" "name" }}-init
        image: {{ .Values.global.registry.url }}/{{ .Values.images.repoPath }}/{{ index .Values "images" "waitInitContainer" "name" }}:{{ index .Values "images" "waitInitContainer" "tag" }}
        imagePullPolicy: {{ .Values.imageCredentials.pullPolicy }}
        command: {{ index .Values "images" "waitInitContainer" "command" }}
{{- end }}
{{- if or .Values.nodeSelector .Values.global.nodeSelector }}
      nodeSelector:
{{- if .Values.nodeSelector }}
{{ toYaml .Values.nodeSelector | indent 8 }}
{{- end }}
{{- if .Values.global.nodeSelector }}
{{ toYaml .Values.global.nodeSelector | indent 8 }}
{{- end }}
{{- end }}
{{- if or .Values.tolerations .Values.global.tolerations }}
      tolerations:
{{- if .Values.tolerations }}
{{ toYaml .Values.tolerations | indent 8 }}
{{- end }}
{{- if .Values.global.tolerations }}
{{ toYaml .Values.global.tolerations | indent 8 }}
{{- end }}
{{- end }}
      containers:
      - name: {{ index .Values "<custom-model-job-values>" "name" }}
        image: {{ .Values.global.registry.url }}/{{ .Values.images.repoPath }}/{{ index .Values "images" "<custom-model-image>" "name" }}:{{ index .Values "images" "<custom-model-image>" "tag" }}
        imagePullPolicy: {{ .Values.imageCredentials.pullPolicy }}
        env:
          - name: TZ
            value: {{ .Values.global.timezone }}
          - name: NAMESPACE
            valueFrom:
              fieldRef:
                fieldPath: metadata.namespace
        resources:
          requests:
            memory: {{ index .Values "<custom-model-job-values>" "memoryRequest" | default "768Mi" }}
            cpu: {{ index .Values "<custom-model-job-values>" "cpuRequest" | default "500m" }}
          limits:
            memory: {{ index .Values "<custom-model-job-values>" "memoryLimit" | default "1Gi" }}
            cpu: {{ index .Values "<custom-model-job-values>" "cpuLimit" | default "1000m" }}
{{- if .Values.mdtPersistentVolumeClaim.enabled }}
        volumeMounts:
        - name: {{ .Values.mdtPersistentVolumeClaim.name }}
          mountPath: {{ .Values.mdtPersistentVolumeClaim.mountPath }}
      volumes:
      - name: {{ .Values.mdtPersistentVolumeClaim.name }}
        persistentVolumeClaim:
          claimName: {{ .Values.mdtPersistentVolumeClaim.claimName }}
{{- end }}
```
