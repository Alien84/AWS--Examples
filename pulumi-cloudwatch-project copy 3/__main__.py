"""Amazon CloudWatch: Monitoring and Observability of AWS Resources with Pulumi"""

"""
Amazon CloudWatch is a monitoring and observability service provided by AWS that gives you actionable insights into your applications, 
responds to system-wide performance changes, optimizes resource utilization, and gets a unified view of operational health.
"""

import pulumi
from pulumi_aws import cloudwatch

# Create a metric alarm
cpu_alarm = cloudwatch.MetricAlarm('cpu-high-alarm',
    comparison_operator='GreaterThanThreshold',
    evaluation_periods=1,
    metric_name='CPUUtilization',
    namespace='AWS/EC2',
    period=60,
    statistic='Average',
    threshold=80.0,
    alarm_description='Alarm when server CPU exceeds 80%',
    dimensions={'InstanceId': 'i-1234567890abcdef0'},  # replace with your instance ID
    actions_enabled=True)

# Create a dashboard
dashboard = cloudwatch.Dashboard('my-dashboard',
    dashboard_name='MyDashboard',
    dashboard_body=pulumi.Output.all(cpu_alarm.arn).apply(lambda arn: json.dumps({
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-west-2",
                    "title": "EC2 Instance CPU Utilization"
                }
            }
        ]
    })))

# Export the dashboard name
pulumi.export('dashboard_name', dashboard.dashboard_name)

"""
Consider implementing best practices such as:
- Comprehensive Coverage: Set up alarms for all critical metrics across your AWS services.
- Notification Actions: Configure actions for alarms, such as notifications through Amazon SNS.
- Logging: Integrate CloudWatch with AWS CloudTrail for comprehensive logging of API calls.
"""