# Use the official Python image as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the script and requirements file into the container
COPY weather-script.py /app/
COPY requirements.txt /app/

RUN apt update && \
    apt install -y curl dnsutils
# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the Python script when the container starts
CMD ["python", "weather-script.py"]
