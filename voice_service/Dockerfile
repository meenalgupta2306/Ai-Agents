# Start from a base image (Python 3.11)
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# 1. Add ffmpeg
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy the application code
COPY . .

# Expose the port
EXPOSE 5002

# Run the application
CMD ["python", "voice_service.py"]