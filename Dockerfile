FROM python:3.12.11-alpine3.22

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY src/ .

# Expose the webhook port
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
