# Copyright ©️ 2025 THEETOX


"""
Image Processor Module
Handles image processing for coin logos.
"""

import io
from PIL import Image

def compress_image(image_bytes, target_size=(512, 512), format="PNG"):
    """
    Compress and resize an image to the target size.
    
    Args:
        image_bytes: The image as bytes
        target_size: The target size as (width, height)
        format: The output format (PNG, JPEG, etc.)
        
    Returns:
        The compressed image as bytes
    """
    # Open the image from bytes
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if needed (removing alpha channel)
    if image.mode == 'RGBA':
        # Create a white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        # Paste the image on the background using alpha as mask
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize the image
    image = image.resize(target_size, Image.LANCZOS)
    
    # Save the image to bytes
    output = io.BytesIO()
    image.save(output, format=format, optimize=True, quality=85)
    output.seek(0)
    
    return output.getvalue()
