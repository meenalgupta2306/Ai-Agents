FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# 1. Add ffmpeg
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the application code
COPY . .

# Expose the port
EXPOSE 3001

# The production way to start a Flask app:
# -w 4 "start 4 workers"
# -b "bind to port 3001"
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3001", "app:app"]
