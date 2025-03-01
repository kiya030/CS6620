import boto3
import json
import time
import requests

# AWS Clients
s3_client = boto3.client("s3")
bucket_name = "test-bucket-ps2-zz"  # Change if needed

# Set your plotting Lambda API endpoint (update after deployment)
PLOTTING_LAMBDA_API = "https://ntkqdbf906.execute-api.us-west-1.amazonaws.com/prod/plot"

def lambda_handler(event, context):
    try:
        print("🚀 Driver Lambda started.")

        # Step 1: Create `assignment1.txt`
        print("📄 Creating 'assignment1.txt'...")
        s3_client.put_object(Bucket=bucket_name, Key="assignment1.txt", Body="Empty Assignment 1")
        time.sleep(5)  # Wait 5 seconds

        # Step 2: Update `assignment1.txt`
        print("✏️ Updating 'assignment1.txt'...")
        s3_client.put_object(Bucket=bucket_name, Key="assignment1.txt", Body="Empty Assignment 2222222222")
        time.sleep(5)  # Wait 5 seconds

        # Step 3: Delete `assignment1.txt`
        print("🗑️ Deleting 'assignment1.txt'...")
        s3_client.delete_object(Bucket=bucket_name, Key="assignment1.txt")
        time.sleep(5)  # Wait 5 seconds

        # Step 4: Create `assignment2.txt`
        print("📄 Creating 'assignment2.txt'...")
        s3_client.put_object(Bucket=bucket_name, Key="assignment2.txt", Body="33")
        time.sleep(5)  # Wait 5 seconds

        # Step 5: Call the Plotting Lambda API
        print("📊 Calling Plotting Lambda API...")
        response = requests.get(PLOTTING_LAMBDA_API)
        print(f"✅ Plotting Lambda Response: {response.text}")

        return {"statusCode": 200, "body": "Driver Lambda executed successfully"}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
