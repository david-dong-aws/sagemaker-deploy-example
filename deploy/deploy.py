"""
Python script to create a SageMaker endpoint from models trained elsewhere
The original model code that used the Algorithmia APIs were rewritten
Endpoint and model specific parameters are defined in the config yaml file
"""

import yaml
import argparse
import boto3
import time
import logging
from sagemaker.model import Model
from sagemaker.session import Session

logger = logging.getLogger(__name__)

# Pass config file as argument
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config_file", 
                    help="Name of the config file", 
                    default='config.yaml')
ARGS = parser.parse_args()

# Parameters from config file
with open(ARGS.config_file, 'r') as f:
    SM_PARAMS = yaml.safe_load(f)

print('Authenticating...')
# Get AWS authentication from environment variables. 
# Change this to how your pipeline log in to the account
# boto_session = boto3.Session(
#     aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
#     aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
#     region_name=SM_PARAMS['region']
# )
boto_session = boto3.Session()
sm_client = boto_session.client('sagemaker')
sm_session = Session(boto_session)


def main():
    """
    Create SM model, endpoint configuration, and endpoint
    using the parameters in the config file
    """
    
    print('Creating model object...')

    # Use vpc settings if given
    if SM_PARAMS['vpc_config']['subnets'][0] is None:
        vpc_config = None
    else:
        vpc_config = {
            'Subnets': SM_PARAMS['vpc_config']['subnets'],
            'SecurityGroupIds': SM_PARAMS['vpc_config']['security_groups']
        }

    # Specify the location for the model code so that it can be picked by terraform
    code_location = f"s3://{SM_PARAMS['output_bucket']}/model-source-code"

    # Create model object. Will override existing one
    model = Model(
        sagemaker_session=sm_session,
        image_uri=SM_PARAMS['image_uri'],
        model_data=SM_PARAMS['model_data_uri'],
        role=SM_PARAMS['sagemaker_role'],
        name=SM_PARAMS['model_name'],
        source_dir=SM_PARAMS['source_dir'],
        entry_point='inference.py',
        code_location=code_location,
        env={"OUTPUT_BUCKET": SM_PARAMS['output_bucket']},
        vpc_config=vpc_config
    )
    # Remove the model object if exist. Otherwise the environment variable
    # won't update for an existing model
    try:
        sm_session.delete_model(model_name=SM_PARAMS['model_name'])
    except Exception as e:
        pass
    # during create() the source code is uploaded/replaced in s3
    model.create() 
    
    print('Creating endpoint config...')
    endpoint_name = SM_PARAMS['endpoint_name']
    # Create endpoint config
    endpoint_config_name = sm_session.create_endpoint_config(
        name=f"{endpoint_name}-{str(round(time.time()))}",
        model_name=SM_PARAMS['model_name'],
        initial_instance_count=SM_PARAMS['instance_count'],
        instance_type=SM_PARAMS['instance_type'],
        volume_size=30
    )


    # Remove failed endpoint before updating
    try:
        status = sm_client.describe_endpoint(EndpointName=endpoint_name)['EndpointStatus']
        if status == 'Failed':
            sm_client.delete_endpoint(EndpointName=endpoint_name)
            sm_client.get_waiter("endpoint_deleted").wait(EndpointName=endpoint_name)
    except:
        pass

    # Add tags to the endpoint so it's easy to find the items for deploy to higher environments
    tags = [
        {
            'Key': 'model_data_location',
            'Value': SM_PARAMS['model_data_uri']
        },
        {
            'Key': 'model_code_location',
            'Value': f"{code_location}/{SM_PARAMS['model_name']}/sourcedir.tar.gz"
        },
        {
            'Key': 'image_uri',
            'Value': SM_PARAMS['image_uri']
        }
    ]
    # Update the existing endpoint if it exists or create a new one
    try:
        endpoint_arn = sm_client.describe_endpoint(EndpointName=endpoint_name)['EndpointArn']
        print('Updating endpoint...')
        sm_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        sm_client.add_tags(ResourceArn=endpoint_arn,
                           Tags=tags)
    except Exception as e:
        try:
            print('Creating endpoint...')
            sm_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
                Tags=tags
            )
        except Exception as e:
            logger.info(e)

    # Wait for endpoint to create
    try:
        sm_client.get_waiter("endpoint_in_service").wait(EndpointName=endpoint_name)
    finally:
        status = sm_client.describe_endpoint(EndpointName=endpoint_name)['EndpointStatus']
        print("Endpoint creation ended with status: " + status)
        if status == "Failed":
            message = sm_client.describe_endpoint(EndpointName=endpoint_name)["FailureReason"]
            print(f"Endpoint failed with the following error: {message}")
            raise Exception(f"Endpoint failed with the following error: {message}")


# Use SageMaker SDK to create endpoint
if __name__ == "__main__":
    main()
