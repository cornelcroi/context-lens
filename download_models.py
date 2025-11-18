#!/usr/bin/env python3
"""
Pre-download embedding models during Docker build.
This prevents cold start timeouts in Lambda.
"""

import os
import sys
from sentence_transformers import SentenceTransformer

def download_model():
    """Download the embedding model to cache."""
    # Model name (must match what's used in your code)
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Cache directory (Lambda can read from /var/task)
    cache_dir = os.getenv("EMBEDDING_CACHE_DIR", "/var/task/models")
    
    print(f"📥 Downloading model: {model_name}")
    print(f"📁 Cache directory: {cache_dir}")
    
    try:
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Download and cache the model
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        
        print(f"✅ Model downloaded successfully!")
        print(f"📊 Model size: {sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(cache_dir) for filename in filenames) / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    download_model()