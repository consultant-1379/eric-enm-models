# ERIC-ENM-Models

This project provides two re-usable model delivery images that can be used to deploy models in a Kubernetes deployment.

This project is also responsible for the creation and delivery of the model deployment images used in ENM:

* Service Models
* Network Resource Models (NRMs)
* Post-Install Models

## Creating & Deploying Model Delivery Images

The core model image **eric-enm-models-core-image** is used to deploy models not in an ENM ISO.
For more information on how to use this image to build and deploy your own custom model image please refer to the following:

* [Deployment of Custom Models not in ENM](/docs/DEPLOYMENT_OF_CUSTOM_MODELS_NOT_IN_ENM.md)


The base model image **eric-enm-models-base-image** can be used to deploy models existing in the ENM ISO.
For more information on how to use this image to build and deploy your own custom model image please refer to the following:

* [Creation of Custom Model Images](/docs/CREATE_CUSTOM_MODEL_IMAGES.md)
* [Deployment of Custom Model Images](/docs/DEPLOY_CUSTOM_MODEL_IMAGES.md)
