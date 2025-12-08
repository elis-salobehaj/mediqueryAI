# Ollama Dockerfile with curl for health checks
FROM ollama/ollama:latest

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Expose Ollama port
EXPOSE 11434

# Use the default Ollama entrypoint
ENTRYPOINT ["/bin/ollama"]
CMD ["serve"]
