"""Amazon SageMaker: Building and Deploying Machine Learning Models with Pulumi"""

"""
Amazon SageMaker is a fully managed service that provides every developer and data scientist with the ability to build, train, and deploy machine learning models quickly.
"""

import pulumi
from pulumi_aws import sagemaker

# Create a SageMaker model
model = sagemaker.Model('my-model',
    execution_role_arn='arn:aws:iam::123456789012:role/SageMakerRole',  # Replace with your IAM role ARN
    primary_container={
        'image': '174872318107.dkr.ecr.us-west-2.amazonaws.com/linear-learner:latest',  # Specify the algorithm image
        'modelDataUrl': 's3://my-bucket/my-model/model.tar.gz'  # Specify the S3 path to your model data
    })

# Create a SageMaker training job
training_job = sagemaker.TrainingJob('my-training-job',
    training_job_name='MyTrainingJob',
    role_arn=model.execution_role_arn,
    algorithm_specification={
        'trainingImage': '174872318107.dkr.ecr.us-west-2.amazonaws.com/linear-learner:latest',
        'trainingInputMode': 'File'
    },
    input_data_config=[{
        'channelName': 'train',
        'dataSource': {
            's3DataSource': {
                's3DataType': 'S3Prefix',
                's3Uri': 's3://my-bucket/my-data/train',
                's3DataDistributionType': 'FullyReplicated'
            }
        },
        'contentType': 'text/csv'
    }],
    output_data_config={
        's3OutputPath': 's3://my-bucket/my-model-output'
    },
    resource_config={
        'instanceType': 'ml.m4.xlarge',
        'instanceCount': 1,
        'volumeSizeInGb': 50
    },
    stopping_condition={'maxRuntimeInSeconds': 3600})

# Create a SageMaker endpoint
endpoint = sagemaker.Endpoint('my-endpoint',
    endpoint_name='MyEndpoint',
    endpoint_config_name=model.name)

# Export the endpoint name
pulumi.export('endpoint_name', endpoint.endpoint_name)
