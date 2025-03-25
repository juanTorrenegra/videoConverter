from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
# ... (keep other imports)

@app.get("/download/")
def download(url: str, format: str = "mp4"):
    try:
        # ... (keep your existing download and upload code)
        
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