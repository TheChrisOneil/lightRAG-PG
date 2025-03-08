# Use arm64 Python base image
FROM arm64v8/python:3.10-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-wheel \
    gfortran \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    curl \
    cmake \
    libssl-dev \
    autoconf \
    automake \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for compiling graspologic-native)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"
RUN rustup default stable

# Upgrade pip, setuptools, and wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel Cython

RUN pip install --no-cache-dir --prefer-binary numpy gensim
RUN pip install --no-cache-dir --prefer-binary graspologic

# Copy requirements file
COPY requirements.txt .
COPY lightrag/api/requirements.txt ./lightrag/api/requirements.txt

# Install Python dependencies globally in /usr/local (not /root/.local)
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/lightrag/api/requirements.txt

# Final stage: Use a smaller runtime image
FROM arm64v8/python:3.10-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /root/.cargo /root/.cargo

# Ensure correct paths
ENV PATH="/usr/local/bin:/root/.cargo/bin:$PATH"
ENV PYTHONPATH="/usr/local/lib/python3.10/site-packages"

# Copy application files
COPY ./lightrag ./lightrag
COPY setup.py .

# Install Python package
RUN pip install --no-cache-dir .

# Expose the default port
EXPOSE 9621

# Set entrypoint
ENTRYPOINT ["python", "-m", "lightrag.api.lightrag_server"]