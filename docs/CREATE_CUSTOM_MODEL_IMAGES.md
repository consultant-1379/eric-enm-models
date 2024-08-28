# Creation of Custom Model Images

[TOC]

This document is a guide to aid a user in creating a model delivery image.

## Base Model Image

The base model image provides the required utilities and instructions to install models during image build time and deploy models during
container run time.

This image is provided/tagged as *armdocker.rnd.ericsson.se/proj-enm/eric-enm-models-base-image:<x.y.z-b>*  
Versions for this image follow the x.y.z-b format and the latest can be found on [gerrit](https://gerrit-gamma.gic.ericsson.se/gitweb?p=OSS%2Fcom.ericsson.oss.cloudcommon.models%2Feric-enm-models.git;a=summary).

### Configuring Image Build

To install and deploy the required models, some configuration must be supplied to the image build:

* *models_dir*: The value used should match the directory in which your model RPM installs its jars, "install" or "post_install". This argument is mandatory.
* *models_type*: The value used for custom model images should be some unique identifier, such as the service name or feature name for which the models are being deployed. This argument is mandatory.
* *model_deploy_file*: This argument is the path to the json file describing which should be installed from the ENM ISO. The default value is "image_content/model_rpms/model-deploy.json".

### Example Configuration

The following steps must be followed to create the image:

* Create a dockerfile that uses the base model image as it's parent
* Write a model-deploy.json file detailing the model RPMs to install
* Configure the building of the image with the necessary arguments

#### Sample Repository Structure

```
|-- Dockerfile
|-- image_content
|   `-- model_rpms
|       `-- model-deploy.json
```

#### Sample Dockerfile

```
ARG ERIC_ENM_MODELS_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-enm
ARG ERIC_ENM_MODELS_IMAGE_NAME=eric-enm-models-base-image
ARG ERIC_ENM_MODELS_IMAGE_TAG=x.y.z-b

FROM ${ERIC_ENM_MODELS_IMAGE_REPO}/${ERIC_ENM_MODELS_IMAGE_NAME}:${ERIC_ENM_MODELS_IMAGE_TAG}
```

**Note**: the naming conventions for the ARGs in the dockerfile are mandatory as they are used 
to automatically update the version of the base image in certain pipelines.

#### Sample model-deploy file

```
{
  "deploy": {
    "rpms": [
      "ERICmyservicenamemodels_CXP1234567",
      "ERICmyservicenameothermodels_CXP12345678"
    ]
  }
}
```

#### Sample Image Build Command

```
docker image build . --build-arg models_dir=install \
--build-arg models_type=ERICmyservicename_CXP7654321 \
--build-arg model_deploy_file=image_content/model_rpms/model-deploy.json \
--tag armdocker.rnd.ericsson.se/proj-enm/my-custom-model-image:x.y.z-b
```

\
This command will trigger a build following the flow of:

* Pulling the parent model image
* Executing the [ONBUILD](https://docs.docker.com/engine/reference/builder/#onbuild) instructions of the parent model image to setup the models for deployment.
* Executing any additional instructions defined in the dockerfile, labels metadata etc.
* Inheriting the [ENTRYPOINT](https://docs.docker.com/engine/reference/builder/#entrypoint) instruction of the parent to be executed at container startup

\
The above sample configuration will create a custom model delivery image
that deploys the RPMs supplied in the model-deploy file.

For further instructions on how to deploy a custom model image, please refer to
[Deployment of Custom Model Images](DEPLOY_CUSTOM_MODEL_IMAGES.md)
