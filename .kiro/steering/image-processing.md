# Image Processing

## Resize Image

```python
from PIL import Image
from io import BytesIO

def resize_image(image_path: str, max_size: tuple) -> BytesIO:
    """Resize image maintaining aspect ratio."""
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    bio = BytesIO()
    img.save(bio, format='JPEG')
    bio.seek(0)
    return bio
```

## Add Watermark

```python
from PIL import ImageDraw, ImageFont

def add_watermark(image_path: str, text: str) -> BytesIO:
    """Add watermark to image."""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Position watermark
    width, height = img.size
    font = ImageFont.truetype("arial.ttf", 36)
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = (width - text_width - 10, height - text_height - 10)
    
    # Draw watermark
    draw.text(position, text, fill=(255, 255, 255, 128), font=font)
    
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio
```

## Convert to Grayscale

```python
def convert_to_grayscale(image_path: str) -> BytesIO:
    """Convert image to grayscale."""
    img = Image.open(image_path).convert('L')
    
    bio = BytesIO()
    img.save(bio, format='JPEG')
    bio.seek(0)
    return bio
```

## Crop Image

```python
def crop_image(image_path: str, box: tuple) -> BytesIO:
    """Crop image to specified box (left, top, right, bottom)."""
    img = Image.open(image_path)
    cropped = img.crop(box)
    
    bio = BytesIO()
    cropped.save(bio, format='JPEG')
    bio.seek(0)
    return bio
```
