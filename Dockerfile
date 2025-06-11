# Use arm64 Python base image
FROM python:3.10-slim as builder

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

# Preinstall some dependencies for speed
RUN pip install --no-cache-dir --prefer-binary numpy gensim
RUN pip install --no-cache-dir --prefer-binary graspologic

# Copy requirements
COPY requirements.txt .
COPY lightrag/api/requirements.txt ./lightrag/api/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/lightrag/api/requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /root/.cargo /root/.cargo

# Set correct paths
ENV PATH="/usr/local/bin:/root/.cargo/bin:$PATH"
ENV PYTHONPATH="/usr/local/lib/python3.10/site-packages"

# Copy application files
COPY ./lightrag ./lightrag
# COPY lightrag/data/prompt_coach_reply_tnc.py ./lightrag/data/prompt_coach_reply_tnc.py
COPY setup.py .

# Install the Python package
RUN pip install --no-cache-dir .

# Expose port
EXPOSE 9621

# Inline pre-start script and launch app
ENTRYPOINT ["/bin/bash", "-c", "\
  mkdir -p /app/data/rag_storage && \
  if [ ! -f /app/data/rag_storage/prompt_coach_reply_tnc.py ]; then \
    echo 'Seeding initial file to /app/data/rag_storage...' && \
    cp /app/lightrag/data/prompt_coach_reply_tnc.py /app/data/rag_storage/; \
  else \
    echo 'File already exists in /app/data/rag_storage. Skipping seeding.'; \
  fi && \
  exec python -m lightrag.api.lightrag_server"]
