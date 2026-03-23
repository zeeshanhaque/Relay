from PIL import Image
import struct
import os

def create_ico(source_path, output_path):
    img = Image.open(source_path).convert("RGBA")
    print(f"Source size: {img.size}")
    
    sizes = [16, 32, 48, 64, 128, 256]
    png_data = []
    
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        import io
        buffer = io.BytesIO()
        resized.save(buffer, format="PNG")
        png_data.append(buffer.getvalue())
    
    # Write ICO file manually
    with open(output_path, "wb") as f:
        # ICO header
        f.write(struct.pack("<HHH", 0, 1, len(sizes)))
        
        # Calculate offsets
        offset = 6 + len(sizes) * 16
        for i, size in enumerate(sizes):
            data = png_data[i]
            f.write(struct.pack("<BBBBHHII",
                size if size < 256 else 0,
                size if size < 256 else 0,
                0, 0, 1, 32,
                len(data), offset
            ))
            offset += len(data)
        
        # Write PNG data
        for data in png_data:
            f.write(data)
    
    print(f"relay.ico created with {len(sizes)} sizes")
    
    # Verify
    with Image.open(output_path) as ico:
        print(f"ICO contains: {ico.info}")

create_ico("resources/icons/relay_icon.png", "resources/icons/relay.ico")