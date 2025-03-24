from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to yt-dlp API"}

@app.get("/download/")
def download(url: str, format: str = "mp4"):
    try:
        command = ["yt-dlp", "-f", format, url]
        result = subprocess.run(command, capture_output=True, text=True)
        return {"output": result.stdout}
    except Exception as e:
        return {"error": str(e)}