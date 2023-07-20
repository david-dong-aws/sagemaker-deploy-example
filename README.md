## Example Jenkins Pipeline for SageMaker Endpoint Deployment

The template provides a starting point to demonstrate how to use Jenkins to orchestrate the creation of SageMaker Endpoints.


## Start here
This repo contains the code for the Jenkins pipeline and parameters for the endpoint.

In jenkins folder:
* seed_job.groovy - this sets up the pipeline definition for the Jenkins job
* Jenkinsfile - for the build, install dependencies and run deploy.py

In deploy folder:
* deploy.py - python script to create or update a SageMaker endpoint
* config.yaml - parameters used by the deploy.py script

In src folder:
* inference.py - skeleton inference code that simply return a message



