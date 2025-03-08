FROM postgres:16

# Install essential dependencies
# Use the PostgreSQL 16 package from the official repository
# Install the PostgreSQL vector extension
# Install the Apache AGE extension dependencies
# Clone and build the Apache AGE extension
RUN apt-get update && apt-get install -y \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    git \
    postgresql-16-pgvector \
    postgresql-server-dev-16 \
    && git clone --depth 1 --branch master https://github.com/apache/age.git /age \
    && cd /age \
    && make PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config install \
    && rm -rf /age

CMD ["postgres"]
