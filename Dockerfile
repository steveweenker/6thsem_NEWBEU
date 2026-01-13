# Use the official Playwright image (Contains Python + All OS Dependencies)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set the working directory
WORKDIR /app

# Copy your files into the container
COPY . .

# Install your Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Install the Chromium browser binary
RUN playwright install chromium

# Run the bot
CMD ["python", "main.py"]
