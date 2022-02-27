import boto3
import xml.etree.ElementTree as ET

import requests

client = boto3.client('sns', region_name='us-west-2')


def assume_role(role_arn):
    global client

    sts_client = boto3.client('sts', region_name='us-west-2')

    assumed_role_obj = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName='SNSBridge',
    )

    credentials = assumed_role_obj['Credentials']

    client = boto3.client('sns',
                          aws_access_key_id=credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey'],
                          aws_session_token=credentials['SessionToken'],
                          region_name='us-west-2')


def subscribe_to_sns(url, sns_endpoint_name, role_arn=None):
    """
    Subscribe a given URL to an SNS endpoint
    :param url: URL to subscribe
    :param sns_endpoint_name: Endpoint name to subscribe to
    :param role_arn: role arn to assume
    :return:
    """
    # TODO: properly handle pagination
    if role_arn:
        assume_role(role_arn)

    topics = client.list_topics()['Topics']
    topic_arn = None

    for topic in topics:
        if sns_endpoint_name in topic['TopicArn']:
            topic_arn = topic['TopicArn']
            break

    results = client.subscribe(TopicArn=topic_arn, Protocol='https', Endpoint=url)

    return results['SubscriptionArn']


def unsubscribe_from_sns(subscription_arn):
    client.unsubscribe(SubscriptionArn=subscription_arn)


def confirm_sns(confirmation_url):
    confirmation = requests.get(confirmation_url)
    node = ET.fromstring(confirmation.content)
    return node[0][0].text
