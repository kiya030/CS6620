import boto3
import json
import time
import requests
import os

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    try:
        print("🚀 Driver Lambda started.")
        bucket_name = os.environ["BUCKET_NAME"]
        plotting_api = os.environ["PLOTTING_LAMBDA_API"]

        print(f"Will store objects in bucket: {bucket_name}")
        print(f"Plot API is at: {plotting_api}")

        # Step 1: Upload assignment1.txt (19 bytes)
        s3_client.put_object(Bucket=bucket_name, Key="assignment1.txt", Body="Empty Assignment 1")
        print("✅ Uploaded assignment1.txt")
        time.sleep(5)

        # Step 2: Upload assignment2.txt (28 bytes) → this should trigger alarm
        s3_client.put_object(Bucket=bucket_name, Key="assignment2.txt", Body="Empty Assignment 22222222222")
        print("✅ Uploaded assignment2.txt (larger)")
        time.sleep(15)

        # Step 3: Upload assignment3.txt (2 bytes)
        s3_client.put_object(Bucket=bucket_name, Key="assignment3.txt", Body="33")
        print("✅ Uploaded assignment3.txt (small)")
        time.sleep(15)

        # Step 4: Trigger plotting lambda via API Gateway
        print(f"📊 Calling Plotting Lambda API at {plotting_api}")
        response = requests.get(plotting_api)
        print(f"✅ Plotting Lambda Response: {response.status_code} - {response.text}")

        return {"statusCode": 200, "body": "Driver Lambda executed successfully"}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
