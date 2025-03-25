from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
import subprocess
import os
import boto3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

app = FastAPI()

# Cloudflare R2 and YouTube config
R2_CONFIG = {
    "endpoint": "https://71a0ff806103c65512db9543fdc4f7ce.r2.cloudflarestorage.com",
    "access_key": "8031c1875c29a19e106b13ca8f82b703",
    "secret_key": "92d96290c2dd54b6510bd4aa60214f9f47f99b8acee0d9a64acca99035295ef1",
    "bucket_name": "videoconverter"
}

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=R2_CONFIG["endpoint"],
    aws_access_key_id=R2_CONFIG["access_key"],
    aws_secret_access_key=R2_CONFIG["secret_key"],
    region_name="auto"
)

# Cookie file path
COOKIES_FILE = "cookies.txt"
COOKIES_DIR = Path("/app/cookies")

@app.on_event("startup")
def create_cookies_dir():
    COOKIES_DIR.mkdir(exist_ok=True)

# Serve index.html
@app.get("/")
def serve_index():
    return FileResponse("index.html")

# New endpoint to upload cookies
@app.post("/upload-cookies/")
async def upload_cookies(file: UploadFile = File(...)):
    try:
        file_path = COOKIES_DIR / COOKIES_FILE
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return {"message": "Cookies uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/")
def download(url: str, format: str = "mp4"):
    try:
        # Validate URL
        if "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        unique_id = uuid.uuid4().hex
        output_filename = f"video_{unique_id}.{format}"
        cookies_path = COOKIES_DIR / COOKIES_FILE
        
        # Build command with cookies if available
        base_command = [
            "yt-dlp",
            "-f", f"bestvideo[ext={format}]+bestaudio[ext=m4a]/best[ext={format}]/best",
            "--add-header", "User-Agent:Mozilla/5.0",
            "--add-header", "Referer:https://www.youtube.com/",
            "--extractor-args", "youtube:player_client=android",
            "--retries", "5",
            "--socket-timeout", "30",
            "-o", output_filename,
            url
        ]
        
        if os.path.exists(cookies_path):
            base_command.extend(["--cookies", str(cookies_path)])
        
        # Execute download
        result = subprocess.run(base_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Download failed: {result.stderr}")

        # Upload to R2 and generate pre-signed URL
        s3_client.upload_file(
            output_filename,
            R2_CONFIG["bucket_name"],
            output_filename,
            ExtraArgs={'ContentType': f'video/{format}'}
        )
        
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': R2_CONFIG["bucket_name"],
                'Key': output_filename
            },
            ExpiresIn=3600
        )

        # Clean up
        try:
            os.remove(output_filename)
        except:
            pass

        return RedirectResponse(presigned_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))