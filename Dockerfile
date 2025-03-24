# Use an official lightweight Python image
FROM python:3.10-slim
# Set the working directory
WORKDIR /app

# Copy all files to the container
COPY . /app

# Install system dependencies (required for yt-dlp and ffmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install yt-dlp
RUN pip install --no-cache-dir yt-dlp

# Expose port 8000
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]