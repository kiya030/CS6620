import boto3
import json
import random
import string
import time

iam_client = boto3.client('iam')
sts_client = boto3.client('sts')

def create_iam_user(user_name):
    """Create an IAM user and generate access keys."""
    user = iam_client.create_user(UserName=user_name)
    creds = iam_client.create_access_key(UserName=user_name)
    return user["User"]["Arn"], creds["AccessKey"]["AccessKeyId"], creds["AccessKey"]["SecretAccessKey"]

def attach_user_policy(user_name):
    """Attach a policy to allow assignment_user to assume Dev and User roles."""
    assume_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "sts:AssumeRole",
                "Resource": [
                    "arn:aws:iam::711387096537:role/Dev",
                    "arn:aws:iam::711387096537:role/User",
                ],
            }
        ],
    }
    iam_client.put_user_policy(
        UserName=user_name,
        PolicyName="AssumeRolesPolicy",
        PolicyDocument=json.dumps(assume_policy),
    )


def create_iam_role(role_name, policy_arn, user_name):
    """Create an IAM role and attach a policy."""
    arn = f"arn:aws:iam::711387096537:user/{user_name}"
    assume_role_policy_document = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS":arn,
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )

    print(json.dumps(json.loads(assume_role_policy_document), indent=4))

    response = iam_client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_document)
    role_arn = response["Role"]["Arn"]
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

    return role_arn


def assume_role(role_arn, session_name, access_key, secret_key):
    """Assume an IAM role using assignment_user's credentials."""
    assignment_session = boto3.session.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    sts_client = assignment_session.client("sts")

    response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    creds = response["Credentials"]

    return boto3.session.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )

def get_user_arn(user_name):
    resp = iam_client.get_user(UserName=user_name)
    return resp['User']['Arn']

def wait_for_user_policy_propagation(user_name, policy_name, max_attempts=10, wait_time=2):
    """Wait until IAM user policy is fully attached"""
    iam_client = boto3.client("iam")

    for attempt in range(max_attempts):
        try:
            response = iam_client.get_user_policy(UserName=user_name, PolicyName=policy_name)
            print(f"✅ Policy {policy_name} is attached to {user_name} (Attempt {attempt + 1})")
            return True
        except iam_client.exceptions.NoSuchEntityException:
            print(f"⏳ Waiting for policy propagation... (Attempt {attempt + 1})")
            time.sleep(wait_time)

    print("❌ Policy propagation timed out!")
    return False

# Step 1: Create IAM user and get credentials
length = 10
user_name = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
user_arn, user_access_key, user_secret_key = create_iam_user(user_name)
print(user_access_key)
print(user_secret_key)

users = iam_client.list_users()
for user in users['Users']:
    print(f"User: {user['UserName']}, ARN: {user['Arn']}")
print(f'waiting create user: {user_name} to propagate...')
time.sleep(10)
# Step 2: Create IAM roles
dev_role_arn = create_iam_role("Dev", "arn:aws:iam::aws:policy/AmazonS3FullAccess", user_name)
user_role_arn = create_iam_role("User", "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess", user_name)
attach_user_policy(user_name)
print(f'waiting attach_user_policy for user: {user_name} to propagate...')
time.sleep(10)
# if wait_for_user_policy_propagation(user_name, 'AssumeRolesPolicy'):
#     print(f"✅ Policy AssumeRolesPolicy is ready!")
# Step 3: Assume Dev role and create S3 bucket & objects
dev_session = assume_role(dev_role_arn, "DevSession", user_access_key, user_secret_key)
s3_client = dev_session.client("s3")

bucket_name = 'my-bucket-' + str(random.randint(0, 1000))
print(bucket_name)
s3_client.create_bucket(Bucket=bucket_name)

files = {
    "assignment1.txt": "Empty Assignment 1",
    "assignment2.txt": "Empty Assignment 2",
}

for file_name, content in files.items():
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=content)

with open("recording1.jpg", "rb") as image:
    s3_client.put_object(Bucket=bucket_name, Key="recording1.jpg", Body=image)

# Step 4: Assume User role and compute total object size
user_session = assume_role(user_role_arn, "UserSession", user_access_key, user_secret_key)
user_s3_client = user_session.client("s3")

response = user_s3_client.list_objects_v2(Bucket=bucket_name, Prefix="assignment")
total_size = sum(obj["Size"] for obj in response.get("Contents", []))
print(f"Total size of 'assignment' objects: {total_size} bytes")

# Step 5: Assume Dev role again and delete objects and bucket
dev_session = assume_role(dev_role_arn, "DevSession", user_access_key, user_secret_key)
s3_client = dev_session.client("s3")
response = user_s3_client.list_objects_v2(Bucket=bucket_name)
objects_to_delete = [{"Key": obj["Key"]} for obj in response.get("Contents", [])]
print(objects_to_delete)
if objects_to_delete:
    s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects_to_delete})

s3_client.delete_bucket(Bucket=bucket_name)