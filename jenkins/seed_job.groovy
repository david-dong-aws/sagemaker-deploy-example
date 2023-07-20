import javaposse.jobdsl.dsl.DslException
import jenkins.model.Jenkins
import hudson.model.AbstractProject

// Check if AWS credential parameter is passed or not
def awsCredentialId = getBinding().getVariables()['AWS_CREDENTIAL']
if (awsCredentialId == null) {
    throw new DslException('Please pass AWS credential parameter ' + 'AWS_CREDENTIAL' )
}

// Sagemaker specific details
def configFileName = "config.yaml"
def awsRegion = 'us-east-1'

// Get git details used in JOB DSL so that can be used for pipeline SCM also
def jobName = getBinding().getVariables()['JOB_NAME']
def gitUrl = getBinding().getVariables()['GIT_URL']
def gitBranch = getBinding().getVariables()['GIT_BRANCH']
def jenkins = Jenkins.getInstance()
def job = (AbstractProject)jenkins.getItem(jobName)
def remoteSCM = job.getScm()
def credentialsId = remoteSCM.getUserRemoteConfigs()[0].getCredentialsId()

pipelineJob("sagemaker-deploy-example") {
    description("Sagemaker Deploy Endpoint Pipeline")
    keepDependencies(false)
    parameters {
        stringParam("CONFIG_FILE_NAME", configFileName, "Name of the configuration file for the endpoint")
        stringParam("AWS_REGION", awsRegion, "Region where project is created")
        credentialsParam("AWS_CREDENTIAL") {
            description("AWS credentials to use for creating entity")
            defaultValue(awsCredentialId)
            type("com.cloudbees.jenkins.plugins.awscredentials.AWSCredentialsImpl")
            required(true)
        }
    }
    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url(gitUrl)
                        credentials(credentialsId)
                    }
                    branch(gitBranch)
                }
            }
            scriptPath("jenkins/Jenkinsfile")
        }
    }
    disabled(false)
    triggers {
        scm("* * * * *")
    }
}