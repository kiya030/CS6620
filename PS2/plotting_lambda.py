import boto3
import json
import time
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os

# AWS Clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

# Constants
TABLE_NAME = "S3-object-size-history"
BUCKET_NAME = "test-bucket-ps2-zz"
PLOT_OBJECT_NAME = "plot.png"

# Fix Matplotlib cache issue in AWS Lambda
os.environ["MPLCONFIGDIR"] = "/tmp"

def get_recent_data():
    """
    Query the last 10 seconds of bucket size data from DynamoDB.
    """
    table = dynamodb.Table(TABLE_NAME)
    
    # Calculate timestamp for 10 seconds ago
    ten_seconds_ago = int(time.time()) - 10
    
    response = table.query(
        KeyConditionExpression="bucket_name = :b AND #ts > :t",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={":b": BUCKET_NAME, ":t": ten_seconds_ago}
    )
    
    return response.get("Items", [])

def get_full_data():
    """
    Query the last 5 minutes of bucket size history.
    Ensures continuity in the line plot.
    """
    table = dynamodb.Table(TABLE_NAME)
    
    five_minutes_ago = int(time.time()) - 300  # Last 5 minutes
    
    response = table.query(
        KeyConditionExpression="bucket_name = :b AND #ts >= :t",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={":b": BUCKET_NAME, ":t": five_minutes_ago}
    )
    
    return response.get("Items", [])

def get_max_size():
    """
    Scan DynamoDB to find the maximum historical bucket size.
    """
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan(ProjectionExpression="total_size")
    
    if not response["Items"]:
        return 0  # No data
    
    return max(int(item["total_size"]) for item in response["Items"])

def generate_plot(data, max_size):
    """
    Generate a plot of bucket size over time (last 10 seconds + history).
    """
    if not data:
        return None  # No data to plot
    
    # Convert timestamps to datetime format
    data.sort(key=lambda x: int(x["timestamp"]))  # Ensure chronological order
    timestamps = [datetime.utcfromtimestamp(int(item["timestamp"])) for item in data]
    sizes = [int(item["total_size"]) for item in data]

    plt.figure(figsize=(8, 5))

    # Get the latest timestamp & limit to last 10 seconds
    latest_time = max(timestamps)
    start_time = latest_time - timedelta(seconds=10)
    plt.xlim(start_time, latest_time)  # Set X-axis range to last 10 seconds

    # Plot bucket size **with line continuity**
    plt.plot(timestamps, sizes, marker="o", linestyle="-", label="Bucket Size", color="blue")
    plt.axhline(y=max_size, color="r", linestyle="--", label="Max Size")

    # **Fix X-axis formatting**
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator(interval=1))  # Show every second
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))  # Show HH:MM:SS
    plt.xticks(rotation=45)  # Rotate labels for clarity

    plt.xlabel("Time (Last 10 Seconds)")
    plt.ylabel("Size (bytes)")
    plt.title("S3 Bucket Size Over Last 10 Seconds")
    plt.legend()
    plt.grid()
    
    # Save to a BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    
    return buf

def upload_to_s3(image_buffer):
    """
    Uploads the generated plot to S3.
    """
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=PLOT_OBJECT_NAME,
        Body=image_buffer,
        ContentType="image/png"
    )
    
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{PLOT_OBJECT_NAME}"

def lambda_handler(event, context):
    """
    Main Lambda function handler.
    """
    recent_data = get_recent_data()
    full_data = get_full_data()  # Fetch last 5 minutes instead of full scan
    max_size = get_max_size()
    
    # Merge datasets for a smooth plot
    all_data = recent_data + full_data
    
    image_buffer = generate_plot(all_data, max_size)
    
    if not image_buffer:
        return {
            "statusCode": 400,
            "body": json.dumps("No data available for plotting.")
        }
    
    plot_url = upload_to_s3(image_buffer)

    return {
        "statusCode": 200,
        "body": json.dumps({"plot_url": plot_url})
    }
