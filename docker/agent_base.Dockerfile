# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash agent && \
    chown -R agent:agent /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/agent/.local/bin:${PATH}"

# Create necessary directories
RUN mkdir -p /app/logs /app/output /app/config && \
    chown -R agent:agent /app/logs /app/output /app/config

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies as non-root user
USER agent
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=agent:agent . .

# Set read-only root filesystem
RUN chmod -R 755 /app && \
    chmod -R 777 /app/logs /app/output /tmp

# Switch back to root for security settings
USER root

# Security hardening
RUN echo "agent ALL=(ALL) NOPASSWD: /usr/bin/pip" >> /etc/sudoers && \
    chmod 440 /etc/sudoers && \
    chown root:root /etc/sudoers && \
    chmod 700 /etc/ssh && \
    chmod 600 /etc/ssh/sshd_config && \
    chmod 600 /etc/ssh/ssh_host_* && \
    chmod 700 /etc/ssh/ssh_host_*_key && \
    chmod 644 /etc/ssh/ssh_host_*_key.pub

# Set up seccomp profile
COPY seccomp.json /etc/docker/seccomp.json

# Set up AppArmor profile
COPY apparmor.conf /etc/apparmor.d/agent

# Set up user namespace mapping
RUN echo "agent:1000:1000" > /etc/subuid && \
    echo "agent:1000:1000" > /etc/subgid

# Switch back to non-root user
USER agent

# Set default command
CMD ["python", "main.py"] 