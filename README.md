Web page that Dockerizes the yt-dlp script, used to download video from an url.


yt-dlp in a main.py script for downloading url
railway.app for deployment
github as source
requirements.txt
Dockerfile for containerization
Cloudflare R" for Cloud Storage > R2 > Create new bucket > 
name/ endpoint/access key ID/ secret access key.

pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
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
pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp

iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], select { width: 100%; padding: 8px; }
        button { padding: 10px 15px; background: #0066ff; color: white; border: none; cursor: pointer; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; border: 1px solid #ddd; }
        .tab.active { background: #0066ff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <h1>YouTube Downloader</h1>
    
    <div class="tabs">
        <div class="tab active" onclick="switchTab('download')">Download Video</div>
        <div class="tab" onclick="switchTab('cookies')">Upload Cookies</div>
    </div>
    
    <div id="download" class="tab-content active">
        <form action="/download/" method="get">
            <div class="form-group">
                <label for="url">YouTube URL:</label>
                <input type="text" id="url" name="url" required>
            </div>
            <div class="form-group">
                <label for="format">Format:</label>
                <select id="format" name="format">
                    <option value="mp4">MP4</option>
                    <option value="best">Best Quality</option>
                </select>
            </div>
            <button type="submit">Download</button>
        </form>
    </div>
    
    <div id="cookies" class="tab-content">
        <form id="cookieForm" enctype="multipart/form-data">
            <div class="form-group">
                <label for="cookiesFile">Cookies File (cookies.txt):</label>
                <input type="file" id="cookiesFile" name="file" accept=".txt" required>
            </div>
            <button type="button" onclick="uploadCookies()">Upload Cookies</button>
        </form>
        <div id="cookieMessage" style="margin-top: 15px;"></div>
        <div style="margin-top: 20px;">
            <h3>How to get cookies:</h3>
            <ol>
                <li>Install the "Get cookies.txt" extension in Chrome</li>
                <li>Login to YouTube in your browser</li>
                <li>Use the extension to export cookies as cookies.txt</li>
                <li>Upload the file here</li>
            </ol>
        </div>
    </div>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelector(`.tab[onclick="switchTab('${tabId}')"]`).classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }

        async function uploadCookies() {
            const fileInput = document.getElementById('cookiesFile');
            const messageDiv = document.getElementById('cookieMessage');
            
            if (fileInput.files.length === 0) {
                messageDiv.textContent = "Please select a file";
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('/upload-cookies/', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (response.ok) {
                    messageDiv.textContent = result.message;
                    messageDiv.style.color = 'green';
                } else {
                    messageDiv.textContent = result.detail || 'Upload failed';
                    messageDiv.style.color = 'red';
                }
            } catch (error) {
                messageDiv.textContent = 'Error uploading cookies';
                messageDiv.style.color = 'red';
            }
        }
    </script>
</body>
</html>
iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii

dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd

dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
