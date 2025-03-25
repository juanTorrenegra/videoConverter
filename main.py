from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import subprocess
import os
import boto3
from botocore.exceptions import NoCredentialsError
import uuid
from datetime import datetime, timedelta

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
    region_name="auto"  # Important for R2
)

# Serve the index.html file
@app.get("/")
def serve_index():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse("index.html")

@app.get("/download/")
def download(url: str, format: str = "mp4"):
    try:
        # Validate URL
        if "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Create unique filename
        unique_id = uuid.uuid4().hex
        output_filename = f"video_{unique_id}.{format}"
        
        # Download with yt-dlp (same as before)
        command = [
            "yt-dlp",
            "-f", f"bestvideo[ext={format}]+bestaudio[ext=m4a]/best[ext={format}]/best",
            "--add-header", "User-Agent:Mozilla/5.0",
            "--add-header", "Referer:https://www.youtube.com/",
            "--extractor-args", "youtube:player_client=android",
            "-o", output_filename,
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Download failed: {result.stderr}")

        # Upload to R2
        try:
            s3_client.upload_file(
                output_filename,
                R2_BUCKET_NAME,
                output_filename,
                ExtraArgs={'ContentType': f'video/{format}'}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        # Generate pre-signed URL (valid for 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': R2_BUCKET_NAME,
                'Key': output_filename
            },
            ExpiresIn=3600
        )

        # Clean up local file
        try:
            os.remove(output_filename)
        except:
            pass

        return RedirectResponse(presigned_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")