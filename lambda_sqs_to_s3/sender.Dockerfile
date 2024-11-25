FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY send_test_message.py .

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Command to run the script
CMD ["python", "send_test_message.py"]
