# Use Microsoft's official Playwright Python image.
# This image includes pre-installed browsers (Chromium, Firefox, WebKit)
# and their system dependencies.
# We use 'latest-noble' which refers to the latest Playwright version
# built on an Ubuntu 'noble' base.
FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

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

# Install your Python dependencies. The 'playwright' package itself will be
# installed from your requirements.txt.
# --no-cache-dir: Prevents pip from caching packages, reducing image size.
# rm -rf /root/.cache: Cleans up any remaining pip cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chromium && \
    rm -rf /root/.cache

# Copy your application code into the container.
# This step is placed after dependency installation to maximize cache efficiency.
COPY . .
RUN chown -R pwuser:pwuser /app
USER pwuser

# Fix permissions for the application directory.
# This is important if you run the container as a non-root user.
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Define the default command to run when the container starts.
# You will typically replace 'bash' with the command to execute your Playwright tests
# or Python script, for example: `CMD ["pytest"]` or `CMD ["python", "your_script.py"]`.
CMD ["bash"]
