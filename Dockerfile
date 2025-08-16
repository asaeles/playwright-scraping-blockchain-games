# Use Microsoft's official Playwright Python image.
# This image includes pre-installed browsers (Chromium, Firefox, WebKit)
# and their system dependencies.
# We use 'latest-noble' which refers to the latest Playwright version
# built on an Ubuntu 'noble' base.
FROM mcr.microsoft.com/playwright/python:latest-noble

# Set environment variables for consistent Python behavior in containers.
# PYTHONDONTWRITEBYTECODE=1: Prevents Python from writing .pyc files.
# PYTHONUNBUFFERED=1: Ensures Python output is unbuffered for real-time logging.
# PLAYWRIGHT_BROWSERS_PATH: Already set correctly in the base image, but kept
# here for clarity of the environment Playwright expects.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set the working directory inside the container for your application.
WORKDIR /app

# Copy your Python requirements file first to leverage Docker's build cache.
# If this file doesn't change, Docker can reuse the layer for pip installation.
COPY requirements.txt .

# Install your Python dependencies. The 'playwright' package itself will be
# installed from your requirements.txt.
# --no-cache-dir: Prevents pip from caching packages, reducing image size.
# rm -rf /root/.cache: Cleans up any remaining pip cache.
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

# The base Microsoft Playwright image already includes Chromium, Firefox, and WebKit
# and their system dependencies, so `playwright install --with-deps` is not needed here
# for browser installation.

# Create a non-root user for security best practices.
# Running Playwright browsers as root is generally not recommended due to sandbox limitations.
# --disabled-password: Ensures the user cannot log in with a password.
# --gecos "": Prevents prompting for user information.
RUN adduser --disabled-password --gecos "" pwuser
# Switch to the newly created non-root user.
# All subsequent commands will run as 'pwuser'.
USER pwuser

# Copy your application code into the container.
# This step is placed after dependency installation to maximize cache efficiency.
COPY . .

# Define the default command to run when the container starts.
# You will typically replace 'bash' with the command to execute your Playwright tests
# or Python script, for example: `CMD ["pytest"]` or `CMD ["python", "your_script.py"]`.
CMD ["bash"]

# Example requirements.txt content that should be in the same directory:
# playwright==1.44.0
# pytest
