# syntax=docker/dockerfile:1
# Prepare the base environment.
FROM python:3.11.10-slim AS builder_base_transcribe
LABEL org.opencontainers.image.authors=ashley@ropable.com
LABEL org.opencontainers.image.source=https://github.com/ropable/podcast-transcriber

RUN apt-get update -y \
  && apt-get upgrade -y \
  && apt-get install -y wget libmagic-dev gcc binutils python3-dev ffmpeg lsb-release software-properties-common gnupg \
  && pip install --root-user-action=ignore --upgrade pip
# We have to install LLVM 15, as this is what llvmlite builds against at present.
RUN wget https://apt.llvm.org/llvm.sh \
  && chmod +x llvm.sh \
  && ./llvm.sh 15
ENV LLVM_CONFIG=/usr/bin/llvm-config-15
RUN rm -rf /var/lib/apt/lists/*

FROM builder_base_transcribe AS python_libs_transcribe
WORKDIR /app
ARG POETRY_VERSION=1.8.4
RUN pip install --root-user-action=ignore --no-cache-dir poetry==${POETRY_VERSION}
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
#
# Set up a non-root user.
ARG UID=10001
ARG GID=10001
RUN groupadd -g ${GID} appuser \
  && useradd --no-create-home --no-log-init --uid ${UID} --gid ${GID} appuser

# Install the project.
FROM python_libs_transcribe
COPY transcriber.py ./
USER ${UID}
