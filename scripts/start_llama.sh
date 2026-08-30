#!/bin/sh
# Start llama.cpp's OpenAI-compatible server using the local cache.
# Anima then: anima --brain llama_cpp
set -e
MODEL="${1:-JonathanColetti/Qwen3.8-27B-Uncensored-GGUF:IQ4_XS}"
exec llama-server --port 8080 --jinja -hf "$MODEL"
