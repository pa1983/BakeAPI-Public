# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stage 1: The "Builder" Stage
#
# In this stage, we install all Python dependencies, including any that might
# require compilation. This keeps our final image clean, as build tools
# and development libraries won't be included in the runtime stage.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# changed from docker hub images to ECR images - builds that ran locally were failing due to the
# rate limits imposed by docker hub on individual IP address.  ECR repos get around this.
FROM public.ecr.aws/docker/library/python:3.13 AS builder

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for Python
# 1. PYTHONUNBUFFERED: Ensures that Python output (like print statements) is
#    sent straight to the terminal without being buffered, which is useful for logging.
# 2. PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk,
#    which isn't necessary in a containerized environment.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies that might be needed for building Python packages
# (e.g., for compiling C extensions in packages like numpy or psycopg2).
# We use --no-install-recommends to keep the layer small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# First, copy only the requirements file to leverage Docker's layer caching.
# If requirements.txt doesn't change, Docker will reuse the cached layer from
# the next step, making subsequent builds much faster.
COPY requirements.txt .

# Install Python dependencies into a virtual environment.
# Using a virtual environment is a good practice even inside a container
# to avoid conflicts with system-level Python packages.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stage 2: The "Runtime" Stage
#
# This is the final image that will be deployed. It's built from a clean
# Python base and only contains the installed dependencies and our app code.
# It's much smaller and more secure than the builder stage.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm AS runtime

# Set the working directory
WORKDIR /app

# Create a non-root user and group for security purposes.
# Running applications as a non-root user is a critical security best practice.
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the builder stage.
# We also ensure the new 'app' user owns these files.
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Copy the application code into the container.
# Make sure the 'app' user owns the application code.
COPY --chown=app:app . .

# Set the environment path to include the virtual environment's bin directory
ENV PATH="/opt/venv/bin:$PATH"

# Switch to the non-root user
USER app

# Expose the port your application will run on.
# This is documentation; you still need to map it with `docker run -p`.
EXPOSE 8000

# Define the command to run your application.
# This is the command that will be executed when the container starts.
# Replace `your_app:app` with your actual file and application instance name.
# For example, for a FastAPI app in `main.py`, it would be:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# For a simple script `main.py`:
# CMD ["python", "main.py"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]