# Ollama Dockerfile with curl for health checks
FROM ollama/ollama:latest

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Expose Ollama port
EXPOSE 11434

# Copy the entrypoint script
COPY ollama_entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
