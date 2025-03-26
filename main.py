from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
import subprocess
import os
import boto3
import uuid
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

# Upload cookies
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
        
        # Build yt-dlp command
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

        # Upload to Cloudflare R2
        s3_client.upload_file(
            output_filename,
            R2_CONFIG["bucket_name"],
            output_filename,
            ExtraArgs={'ContentType': f'video/{format}'}
        )
        
        # Generate pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': R2_CONFIG["bucket_name"],
                'Key': output_filename
            },
            ExpiresIn=3600
        )

        # Clean up local file
        try:
            os.remove(output_filename)
        except:
            pass

        # Return styled HTML response with download button
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download Ready</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #333;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                .flower-container {{
                    margin: 30px 0;
                    height: 200px;
                }}
                .flower {{
                    height: 100%;
                }}
                .download-btn {{
                    display: inline-block;
                    padding: 15px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    font-size: 1.2em;
                    border-radius: 5px;
                    margin-top: 20px;
                    transition: all 0.3s ease;
                }}
                .download-btn:hover {{
                    background-color: #45a049;
                    transform: scale(1.05);
                }}
                .loading {{
                    display: none;
                    margin: 20px auto;
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #3498db;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <h1>Your Download Is Ready!</h1>
            <div class="flower-container">
                <img src="https://media.giphy.com/media/XpgOZHuXjQ3bO/giphy.gif" class="flower" alt="Flower animation">
            </div>
            <a href="{presigned_url}" class="download-btn" download>Download Video</a>
        </body>
        </html>
        """)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))