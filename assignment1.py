import boto3
import json

iam_client = boto3.client('iam')
sts_client = boto3.client('sts')

def create_iam_role(role_name, policy_arn):
    assume_role_policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "sts:AssumeRole"
            }
        ]
    })

    response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=assume_role_policy_document
    )
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    return response['Role']['Arn']

dev_role_arn = create_iam_role("Dev", "arn:aws:iam::aws:policy/AmazonS3FullAccess")
user_role_arn = create_iam_role("User", "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess")

user_name = "assignment_user"
iam_client.create_user(UserName=user_name)

def assume_role(role_arn, session_name):
    response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    creds = response['Credentials']
    return boto3.session.Session(
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
    )

dev_session = assume_role(dev_role_arn, "DevSession")
s3_client = dev_session.client('s3')

bucket_name = "my-unique-assignment-bucket"
s3_client.create_bucket(Bucket=bucket_name)

files = {
    "assignment1.txt": "Empty Assignment 1",
    "assignment2.txt": "Empty Assignment 2"
}

for file_name, content in files.items():
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=content)

image_path = "recording1.jpg"
with open(image_path, "rb") as image:
    s3_client.put_object(Bucket=bucket_name, Key="recording1.jpg", Body=image)

user_session = assume_role(user_role_arn, "UserSession")
user_s3_client = user_session.client('s3')

response = user_s3_client.list_objects_v2(Bucket=bucket_name, Prefix="assignment")
total_size = sum(obj["Size"] for obj in response.get("Contents", []))

dev_session = assume_role(dev_role_arn, "DevSession")
s3_client = dev_session.client('s3')

objects_to_delete = [{"Key": obj["Key"]} for obj in response.get("Contents", [])]
if objects_to_delete:
    s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects_to_delete})

s3_client.delete_bucket(Bucket=bucket_name)
