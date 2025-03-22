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

        # Step 1: Create `assignment1.txt`
        s3_client.put_object(Bucket=bucket_name, Key="assignment1.txt", Body="Empty Assignment 1")
        time.sleep(5)

        # Step 2: Update `assignment1.txt`
        s3_client.put_object(Bucket=bucket_name, Key="assignment1.txt", Body="Empty Assignment 2222222222")
        time.sleep(5)

        # Step 3: Delete `assignment1.txt`
        s3_client.delete_object(Bucket=bucket_name, Key="assignment1.txt")
        time.sleep(5)

        # Step 4: Create `assignment2.txt`
        s3_client.put_object(Bucket=bucket_name, Key="assignment2.txt", Body="33")
        time.sleep(5)

        # Step 5: Call the Plotting Lambda API
        print(f"📊 Calling Plotting Lambda API at {plotting_api}")
        response = requests.get(plotting_api)
        print(f"✅ Plotting Lambda Response: {response.text}")

        return {"statusCode": 200, "body": "Driver Lambda executed successfully"}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
