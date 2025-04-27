"""Amazon SQS: Integrating Message Queuing with Pulumi"""

"""
Amazon Simple Queue Service (SQS) offers a secure, durable, and available hosted queue that lets you integrate and decouple distributed software systems and components. 
This chapter will guide you through creating and managing SQS queues using Pulumi, which provides a declarative way to define and deploy AWS resources programmatically.
"""

import pulumi
from pulumi_aws import sqs
import json

"""
This setup creates two queues: a primary queue where messages are initially sent and 
a dead-letter queue for messages that fail to be processed after several attempts. 
The redrive policy automatically moves messages to the dead-letter queue after a specified number of failed processing attempts.
"""

# Create a standard SQS queue
main_queue = sqs.Queue('my-main-queue',
    delay_seconds=10,
    max_message_size=262144,
    message_retention_seconds=86400)  # 1 day

# Create a dead-letter queue
dead_letter_queue = sqs.Queue('my-dead-letter-queue',
    message_retention_seconds=1209600)  # 14 days

# Create a redrive policy on the main queue to use the dead-letter queue
redrive_policy = pulumi.Output.all(main_queue.arn, dead_letter_queue.arn).apply(lambda args: json.dumps({
    "deadLetterTargetArn": args[1],
    "maxReceiveCount": 5
}))

main_queue_redrive_policy = sqs.Queue('my-main-queue-with-redrive',
    delay_seconds=10,
    max_message_size=262144,
    message_retention_seconds=86400,  # 1 day
    redrive_policy=redrive_policy)

"""
Best Practices and Additional Configurations
Consider implementing best practices such as:
- Visibility Timeout: Adjust the visibility timeout setting to ensure that messages are processed completely before they become visible again in the queue.
- Encryption: Enable encryption at rest to secure your messages.
- Monitoring: Set up CloudWatch alarms to monitor the number of messages sent, received, and the age of the oldest message in the queue.
"""