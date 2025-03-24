from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os

app = FastAPI()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import subprocess
import os
import boto3
from botocore.exceptions import NoCredentialsError

app = FastAPI()

# Cloudflare R2 credentials
R2_ENDPOINT = "https://71a0ff806103c65512db9543fdc4f7ce.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "8031c1875c29a19e106b13ca8f82b703"
R2_SECRET_KEY = "92d96290c2dd54b6510bd4aa60214f9f47f99b8acee0d9a64acca99035295ef1"
R2_BUCKET_NAME = "videoconverter"

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

# Serve the index.html file
@app.get("/")
def serve_index():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse("index.html")

# Download endpoint
@app.get("/download/")
def download(url: str, format: str = "mp4"):
    try:
        # Run yt-dlp to download the video
        output_filename = "video.mp4"
        command = ["yt-dlp", "-f", format, "-o", output_filename, url]
        result = subprocess.run(command, capture_output=True, text=True)

        # Check if the download was successful
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr)

        # Upload the video to Cloudflare R2
        try:
            s3_client.upload_file(output_filename, R2_BUCKET_NAME, output_filename)
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="Cloudflare R2 credentials not configured")

        # Generate a public URL for the uploaded file
        file_url = f"{R2_ENDPOINT}/{R2_BUCKET_NAME}/{output_filename}"

        # Return the download link
        return RedirectResponse(file_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))