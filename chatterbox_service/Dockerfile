# Start from a base image (Python 3.11)
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

#Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Since chatterbox uses torch, we ensure it's installed (CPU version for now to keep it light)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy the application code
COPY . .

# Expose the port
EXPOSE 5003

# Run the application
CMD ["python", "chatterbox_service.py"]
