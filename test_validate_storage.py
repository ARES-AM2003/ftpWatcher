"""
Test script to demonstrate storage validation API call format.
This shows how the validate_storage method formats the request.
"""

import asyncio
from pathlib import Path

# Example: Converting file sizes to GB


def bytes_to_gb(size_bytes: int) -> float:
    """Convert bytes to GB and round to 6 decimal places."""
    size_gb = size_bytes / (1024**3)
    return round(size_gb, 6)


# Example file sizes and their GB equivalents
examples = [
    (100 * 1024 * 1024, "100 MB"),  # 100 MB
    (500 * 1024 * 1024, "500 MB"),  # 500 MB
    (1 * 1024 * 1024 * 1024, "1 GB"),  # 1 GB
    (2.5 * 1024 * 1024 * 1024, "2.5 GB"),  # 2.5 GB
    (107374182, "~100 MB (exact bytes)"),  # Exact bytes
]

print("File Size Conversion Examples:")
print("-" * 60)
for size_bytes, description in examples:
    size_gb = bytes_to_gb(int(size_bytes))
    print(f"{description:25} = {int(size_bytes):12} bytes = {size_gb} GB")

print("\n" + "=" * 60)
print("Example API Request Format:")
print("=" * 60)

# Example request
user_id = "6905548a-b98e-4c33-a101-8f007499d8a1"
total_bytes = 107374182  # ~100 MB
file_keys = [
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/file1.jpg",
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/file2.mp4",
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/file3.jpg",
]

size_gb = bytes_to_gb(total_bytes)

print(f"\ncurl -X 'POST' \\")
print(f"  'https://prod.fotosfolio.com/storage/validate/{user_id}/{size_gb}' \\")
print(f"  -H 'accept: */*' \\")
print(f"  -H 'Authorization: Bearer YOUR_TOKEN' \\")
print(f"  -H 'Content-Type: application/json' \\")
print(f"  -d '{{")
print(f'  "fileKeys": [')
for i, key in enumerate(file_keys):
    comma = "," if i < len(file_keys) - 1 else ""
    print(f'    "{key}"{comma}')
print(f"  ]")
print(f"}}'")

print("\n" + "=" * 60)
print("Python Request Example:")
print("=" * 60)

print(f"""
import aiohttp

url = "https://prod.fotosfolio.com/storage/validate/{user_id}/{size_gb}"
headers = {{
    "accept": "*/*",
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}}
payload = {{
    "fileKeys": {file_keys}
}}

async with aiohttp.ClientSession() as session:
    async with session.post(url, json=payload, headers=headers) as response:
        data = await response.json()
        reservation_id = data.get("reservationId")
        print(f"Reservation ID: {{reservation_id}}")
""")

print("\n" + "=" * 60)
print("File Key Format:")
print("=" * 60)
print("""
File keys follow the format:
  {username_userid}/ftp/{ftp_username}/{filename}

Where:
  - username_userid: e.g., "Test2_6905548a-b98e-4c33-a101-8f007499d8a1"
  - ftp_username: folder name like "camera1", "camera2", etc.
  - filename: actual file name with extension

Examples:
  Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/image.jpg
  Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/video.mp4
  Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/uploads/document.pdf
""")
