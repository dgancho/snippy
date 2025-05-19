# Snippy Functions – Dev Container image
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update \
    && apt-get install -y curl gnupg2 build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Azure Functions Core Tools v4
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g azure-functions-core-tools@4 --unsafe-perm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Azure Developer CLI (azd)
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

RUN azd version

# Install uv (Python package manager)
RUN pip install --no-cache-dir uv

# Optionally copy welcome notice
COPY first-run-notice.txt /usr/local/etc/first-run-notice.txt

WORKDIR /workspaces/app