from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os

app = FastAPI()

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
        command = ["yt-dlp", "-f", format, "-o", "video.mp4", url]
        result = subprocess.run(command, capture_output=True, text=True)

        # Check if the download was successful
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr)

        # Return the download link (this is just a placeholder)
        return {"message": "Download successful", "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))