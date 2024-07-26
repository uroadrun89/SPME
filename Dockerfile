# Start with the base image
FROM ubuntu:18.04

# Install Python 3.11 and pip
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip3.11 install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Start the Python application
# Use the `CMD` instruction to specify the default command to run the application
CMD ["python3.11", "main.py"]

# Expose port 80
EXPOSE 80

# Start an HTTP server to serve the application
CMD ["python3.11", "-m", "http.server", "80"]
