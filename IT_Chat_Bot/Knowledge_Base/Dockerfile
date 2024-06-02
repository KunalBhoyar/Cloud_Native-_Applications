# Use an official Python runtime as a parent image
FROM python:3.9-slim AS builder

WORKDIR /app

# Copy only the requirements file to install dependencies
COPY requirements.txt .
RUN python3 -m venv myenv && \
    /bin/sh -c ". myenv/bin/activate && pip install --no-cache-dir -r requirements.txt"

# Copy the rest of the application files
COPY . .

# Stage 2: Create a minimal runtime image
FROM python:3.9-slim

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /app /app

EXPOSE 80

CMD ["myenv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
