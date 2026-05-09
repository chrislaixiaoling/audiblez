FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    libsox-dev \
    libsndfile1 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements_hf.txt .
RUN pip install --no-cache-dir -r requirements_hf.txt

# Install audiblez from PyPI
RUN pip install --no-cache-dir audiblez

# Download spacy model at build time
RUN python -c "import spacy; spacy.cli.download('xx_ent_wiki_sm')"

# Copy application code
COPY app.py .

# Expose Gradio port
EXPOSE 7860

# Environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

# Run the app
CMD ["python", "app.py"]
