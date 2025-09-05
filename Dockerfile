# Extensive comments included as supplementary documentation

# Builder Stage - Install all Python dependencies in a full python base image.

# changed from docker hub images to ECR images - builds that ran remotely were failing due to the
# rate limits imposed by docker hub on individual IP addresses.  ECR repos get around this as they have no rate
# limits when called from AWS services.
FROM public.ecr.aws/docker/library/python:3.13 AS builder

# Set the working directory inside the container- match the local file structure to make it easier to
# understand the filesystem if debugging within the container
WORKDIR /app

# standard boilerplate Dockerfile behavoiour, included by Pycharm by default:
# Set environment variables for Python
# 1. PYTHONUNBUFFERED: Ensures that Python output (like print statements) is
#    sent straight to the terminal without being buffered, which is useful for logging.
# 2. PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk,
#    which isn't necessary in a containerized environment.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies that might be needed for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file separately and prior to the applciation files to take advantage of Docker's
# dependancy management - if the app code changes but not the requirements.txt (which is less often changed),
# fewer build steps need to be completed to re-created the image
COPY requirements.txt .

# Install Python dependencies into a virtual environment.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Runtime Stage
# The final deployed image is built from a clean Python base and contains on the
# installed dependencies and application code, reducing size.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm AS runtime

# Set the working directory
WORKDIR /app

# Create a non-root user and group for security purposes; running in a non-root user is security best practice.
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Copy the application code into the container, making sure the 'app' user owns the application code.
COPY --chown=app:app . .

# Set the environment path to include the virtual environment's bin directory
ENV PATH="/opt/venv/bin:$PATH"

# Switch to the non-root user
USER app

# Expose the port the application will run on.
EXPOSE 8000

# The command used to run the application; in this case we use uvicorn to run app in main.py, exposing publicly
# (0.0.0.0) on port 8000 (the port exposed above and used within the application)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]