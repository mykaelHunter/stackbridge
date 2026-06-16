import boto3


def validate_aws():

    sts = boto3.client("sts")

    identity = sts.get_caller_identity()

    return identity["Account"]
