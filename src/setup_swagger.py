#!/usr/bin/env python3
"""
Setup script to download Swagger UI assets locally
This ensures no external dependencies at runtime
"""

import os
import urllib.request
import json
from pathlib import Path

def download_swagger_assets():
    """Download Swagger UI assets for offline use"""
    
    # Create static directory
    static_dir = Path("static/swagger-ui")
    static_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading Swagger UI assets...")
    
    # Define assets to download
    assets = {
        "swagger-ui.css": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        "swagger-ui-bundle.js": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        "swagger-ui-standalone-preset.js": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js",
        "favicon.png": "https://fastapi.tiangolo.com/img/favicon.png"
    }
    
    for filename, url in assets.items():
        file_path = static_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename} already exists")
        else:
            try:
                print(f"  Downloading {filename}...")
                urllib.request.urlretrieve(url, file_path)
                print(f"  ✓ {filename} downloaded")
            except Exception as e:
                print(f"  ✗ Failed to download {filename}: {e}")
    
    # Create a custom index.html for Swagger UI
    index_html = """
<!DOCTYPE html>
<html>
<head>
    <link type="text/css" rel="stylesheet" href="/static/swagger-ui/swagger-ui.css">
    <title>V5 AI Engine - API Documentation</title>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
    <script src="/static/swagger-ui/swagger-ui-standalone-preset.js"></script>
    <script>
    window.onload = function() {
        window.ui = SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout"
        })
    }
    </script>
</body>
</html>
"""
    
    index_path = static_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(index_html)
    print("  ✓ Custom index.html created")
    
    print("\nSwagger UI setup complete!")
    print("Assets are stored in: static/swagger-ui/")
    return True

if __name__ == "__main__":
    download_swagger_assets()