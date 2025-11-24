# QR Code Generation

## Generate QR Code

```python
import qrcode
from io import BytesIO

def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
```

## Send QR Code

```python
async def send_qr_code(update, context, data: str):
    """Send QR code to user."""
    qr_image = generate_qr_code(data)
    
    await update.message.reply_photo(
        photo=qr_image,
        caption=f"QR Code for: {data}"
    )
```

## QR Code Command

```python
async def qr_command(update, context):
    """Generate QR code from text."""
    if not context.args:
        await update.message.reply_text("Usage: /qr <text>")
        return
    
    text = " ".join(context.args)
    await send_qr_code(update, context, text)
```

## QR Code with Logo

```python
from PIL import Image

def generate_qr_with_logo(data: str, logo_path: str) -> BytesIO:
    """Generate QR code with logo in center."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make()
    
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Add logo
    logo = Image.open(logo_path)
    logo_size = img.size[0] // 4
    logo = logo.resize((logo_size, logo_size))
    
    pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
    img.paste(logo, pos)
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
```
