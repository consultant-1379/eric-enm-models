# Deployment of Custom Model Images

[TOC]

This document is a guide to aid a user in deploying a custom model image in a Kubernetes environment.

## Deploying Custom Model Images in ENM

Model delivery in a Kubernetes environment should be executed using [Kubernetes Job objects](
https://kubernetes.io/docs/concepts/workloads/controllers/job/).  
Additionally the Job should be deployed as a [Helm Hook](https://helm.sh/docs/topics/charts_hooks/).

To deploy custom models images as part of an ENM Initial Install or Upgrade, a Helm template
must be included in the ENM integration charts. The template must refer to the custom model image
that was built in the previous [Creation of Custom Model Images](CREATE_CUSTOM_MODEL_IMAGES.md) document.

It is required that the Job template is included in the [eric-enm-infra-integration](
https://gerrit-gamma.gic.ericsson.se/plugins/gitiles/OSS/com.ericsson.oss.containerisation/eric-enm-infra-integration)
chart to ensure the models contained in said image will be deployed before the ENM services are brought online.

Before writing the Job template, familiarity with the following Kubernetes and Helm constructs is recommended:

#### Helm flow control

[Helm Flow Control](https://helm.sh/docs/chart_template_guide/control_structures/) should be used to allow for the enabling and disabling of the job
depending on a chosen parameter included in the chart values file. It is mandatory to use if the deployment of the model image is conditional.

### Example Template

The following steps must be followed to create the Job template:

* Add configurations to the chart values file.
* Add a Job template to the *eric-enm-infra-integration* chart to deploy your image.

**Note**: Model job templates should be named following the pattern of ```eric-enm-models-<service-name>.yaml```

#### Sample Values Configuration

The values file of the *eric-enm-infra-integration* chart needs to be updated to describe:

* The custom model image name and tag. Should be appended to the existing 'images' subsection of the chart.
* A new subsection detailing input values used for rendering the Job template.

See example below:
```
images:
  eric-enm-models-custom-service:
    name: eric-enm-models-custom-service
    tag: x.y.z-b

eric-enm-models-custom-service-job:
  name: eric-enm-models-custom-service
  restartPolicy: OnFailure
```

#### Sample Template
The provided template should be modified to reflect the updated values file.
For the sample values file update above:

* ```<custom-model-job-values>``` should be replaced with ```eric-enm-models-custom-service-job```.
* ```<custom-model-image>``` should be replaced with ```eric-enm-models-custom-service```.

**Note**: Other rendered aspects of the template should be resolved within the *eric-enm-infra-integration* chart.

```
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ index .Values "<custom-model-job-values>" "name" }}-job
  labels:
    app: {{ template "infra-integration.name" . }}
    chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
    release: "{{ .Release.Name }}"
    heritage: "{{ .Release.Service }}"
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "-3"
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  template:
    metadata:
      name: {{ index .Values "<custom-model-job-values>" "name" }}-job
      labels:
        app: {{ template "infra-integration.name" . }}
        chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
        release: "{{ .Release.Name }}"
        heritage: "{{ .Release.Service }}"
    spec:
      restartPolicy: {{ index .Values "<custom-model-job-values>" "restartPolicy" }}
{{- if include "infra-integration.pullSecrets" . }}
      imagePullSecrets:
        - name: {{ template "infra-integration.pullSecrets" . }}
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
            memory: {{ .Values.<custom-model-job-values>.memoryRequest | default "768Mi" }}
            cpu: {{ .Values.<custom-model-job-values>.cpuRequest | default "500m" }}
          limits:
            memory: {{ .Values.<custom-model-job-values>.memoryLimit | default "1Gi" }}
            cpu: {{ .Values.<custom-model-job-values>.cpuLimit | default "1000m" }}
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

The template should be wrapped in an if statement should the deployment of the custom model image be conditional.
```
{{- if <condition> }}
<template here>
{{- end }}
```