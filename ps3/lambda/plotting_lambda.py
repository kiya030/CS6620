import boto3
import json
import time
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os

# Fix Matplotlib cache issue in AWS Lambda
os.environ["MPLCONFIGDIR"] = "/tmp"

# AWS Clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

# Read from environment variables set by CDK
TABLE_NAME = os.environ["DYNAMODB_TABLE_NAME"]  # Provided by table.table_name]
BUCKET_NAME = os.environ["BUCKET_NAME"]         # We'll set this in lambda_stack
PLOT_OBJECT_NAME = "plot.png"

def get_recent_data():
    """
    Query the last 10 seconds of bucket size data from DynamoDB.
    """
    table = dynamodb.Table(TABLE_NAME)
    ten_seconds_ago = int(time.time()) - 10
    
    response = table.query(
        KeyConditionExpression="bucket_name = :b AND #ts > :t",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={":b": BUCKET_NAME, ":t": ten_seconds_ago}
    )
    return response.get("Items", [])

def get_full_data():
    """
    Query the last 5 minutes of bucket size history
    so the line plot isn't just the last 10 seconds.
    """
    table = dynamodb.Table(TABLE_NAME)
    five_minutes_ago = int(time.time()) - 300
    
    response = table.query(
        KeyConditionExpression="bucket_name = :b AND #ts >= :t",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={":b": BUCKET_NAME, ":t": five_minutes_ago}
    )
    return response.get("Items", [])

def get_max_size():
    """
    Scan the entire table for the max historical size.
    """
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan(ProjectionExpression="total_size")
    if not response["Items"]:
        return 0
    return max(int(item["total_size"]) for item in response["Items"])

def generate_plot(data, max_size):
    """
    Generate and return a PNG plot in memory (BytesIO).
    """
    if not data:
        return None
    
    data.sort(key=lambda x: int(x["timestamp"]))
    timestamps = [datetime.utcfromtimestamp(int(item["timestamp"])) for item in data]
    sizes = [int(item["total_size"]) for item in data]

    plt.figure(figsize=(8, 5))

    # Show only last 10 seconds on X-axis
    latest_time = max(timestamps)
    start_time = latest_time - timedelta(seconds=10)
    plt.xlim(start_time, latest_time)

    # Plot
    plt.plot(timestamps, sizes, marker="o", linestyle="-", label="Bucket Size")
    plt.axhline(y=max_size, linestyle="--", label="Max Size")

    # Format X-axis
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.xticks(rotation=45)

    plt.xlabel("Time (Last 10 Seconds)")
    plt.ylabel("Size (bytes)")
    plt.title("S3 Bucket Size Over Last 10 Seconds")
    plt.legend()
    plt.grid()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return buf

def upload_to_s3(image_buffer):
    """
    Upload the plot image to S3.
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
    Main Lambda function entry.
    """
    recent_data = get_recent_data()
    full_data = get_full_data()
    max_size = get_max_size()

    # Merge them for a continuous line
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

