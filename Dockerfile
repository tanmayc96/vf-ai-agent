FROM mirror.gcr.io/library/python:3.10.19-slim

# Set environment variables to configure Python and Poetry behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install Poetry from a custom PyPI mirror
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "poetry==$POETRY_VERSION"

# Set the working directory inside the container
WORKDIR /app

# Copy only dependency files first to leverage caching
COPY pyproject.toml poetry.lock* /app/

# Generate the lock file and install dependencies (no-root to avoid installing the package itself yet)
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root --no-ansi

# Copy the rest of the application code
COPY README.md main.py /app/
COPY ngni_agent /app/ngni_agent

# Install the project itself (if it's a package)
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-ansi

ENV PYTHONPATH=/app

# Expose the port used by the application (Cloud Run expects this)
EXPOSE 8080

RUN echo "Build timestamp : $(date)" && ls -R /app

WORKDIR /app

# Start the application using Uvicorn and Poetry
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
