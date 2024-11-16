# Use an official Python image as a base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    libssl-dev \
    libffi-dev \
    git \
    chromium \
    chromium-driver \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir anthropic \
    flask \
    requests \
    selenium \
    fpdf

# Set the environment variable for Chrome driver
ENV CHROME_BIN=/usr/bin/chromium 
ENV CHROME_DRIVER=/usr/bin/chromedriver

# Expose the port the app runs on
EXPOSE 5000

# Command to run your Python script
CMD ["python", "./main.py"]
