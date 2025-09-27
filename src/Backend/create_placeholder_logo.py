#!/usr/bin/env python3
"""Create a placeholder logo for WeedGo tenant"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create uploads directory structure
upload_dir = "/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend/uploads/tenants/ce2d57bc-b3ba-4801-b229-889a9fe9626d/"
os.makedirs(upload_dir, exist_ok=True)

# Create a simple placeholder logo
width = 200
height = 200
img = Image.new('RGB', (width, height), color='#4CAF50')
draw = ImageDraw.Draw(img)

# Draw a circle background
draw.ellipse([20, 20, 180, 180], fill='#388E3C')

# Add text
try:
    # Try to use a system font
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
except:
    font = ImageFont.load_default()

# Draw text
text = "WG"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
position = ((width - text_width) // 2, (height - text_height) // 2 - 10)
draw.text(position, text, fill='white', font=font)

# Save the image
logo_path = os.path.join(upload_dir, "logo.png")
img.save(logo_path)
print(f"Logo created at: {logo_path}")