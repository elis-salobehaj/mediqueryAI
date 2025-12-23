#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
pid=$!

# Wait for Ollama service to start.
echo "Waiting for Ollama service to start..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done

echo "Ollama service started."

# Array of models to pull
models=("qwen3:latest" "gemma3:4b" "qwen2.5:3b")

for model in "${models[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "Model $model already exists."
    else
        echo "Pulling model $model..."
        ollama pull "$model"
    fi
done

# Wait for the Ollama process to exit.
wait $pid
