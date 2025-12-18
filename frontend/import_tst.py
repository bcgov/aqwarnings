import boto3
import os
from datetime import datetime, timedelta, timezone

# Dell ECS credentials and endpoint from environment variables



DELL_ECS_ACCESS_KEY = os.getenv('S3_ACCESS_KEY_ID')
DELL_ECS_SECRET_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
DELL_ECS_ENDPOINT = os.getenv('S3_ENDPOINT')
BUCKET_NAME = os.getenv('S3_BUCKET')

# Optional: restrict to a folder/prefix
PREFIX = ''

LOCAL_FILE_PATH = './frontend/warnings_tst'
LOOKBACK_MINUTES = 10

# Ensure local directory exists
os.makedirs(LOCAL_FILE_PATH, exist_ok=True)

# Initialize the S3 client (Dell ECS compatible)
s3_client = boto3.client(
    's3',
    aws_access_key_id=DELL_ECS_ACCESS_KEY,
    aws_secret_access_key=DELL_ECS_SECRET_KEY,
    endpoint_url=DELL_ECS_ENDPOINT,
    region_name='us-east-1'
)

# Calculate cutoff time (UTC)
cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)

def list_recent_objects(bucket, prefix):
    """List objects modified in the last LOOKBACK_MINUTES."""
    paginator = s3_client.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            if obj['LastModified'] >= cutoff_time:
                yield obj

try:
    recent_objects = list(list_recent_objects(BUCKET_NAME, PREFIX))

    if not recent_objects:
        print(f"No files added or updated in the last {LOOKBACK_MINUTES} minutes.")
        exit(0)

    for obj in recent_objects:
        object_key = obj['Key']
        local_file = os.path.join(
            LOCAL_FILE_PATH,
            os.path.basename(object_key)
        )

        s3_client.download_file(BUCKET_NAME, object_key, local_file)
        print(f"Downloaded: {object_key} → {local_file}")

except Exception as e:
    print(f"Error downloading recent files: {e}")
    raise
