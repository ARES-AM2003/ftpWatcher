"""
Test script to demonstrate presigned URLs API call format.
Shows the correct format for requesting presigned URLs with fileName and contentType.
"""

import json

# Example: Presigned URLs Request Format

print("=" * 70)
print("Presigned URLs API Request Format")
print("=" * 70)

# Example file data
files_data = [
    {
        "fileName": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/image1.jpg",
        "contentType": "image/jpeg",
    },
    {
        "fileName": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/video1.mp4",
        "contentType": "video/mp4",
    },
    {
        "fileName": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/image2.png",
        "contentType": "image/png",
    },
    {
        "fileName": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/document.pdf",
        "contentType": "application/pdf",
    },
]

print("\n📋 Example Files:")
print("-" * 70)
for i, file_info in enumerate(files_data, 1):
    print(f"{i}. {file_info['fileName']}")
    print(f"   Content-Type: {file_info['contentType']}")
    print()

print("=" * 70)
print("cURL Command")
print("=" * 70)

# Build the payload
payload = {"files": files_data}
payload_json = json.dumps(payload, indent=2)

print(f"""
curl -X 'POST' \\
  'https://api.fotosfolio.com/uploads/presigned-urls' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer YOUR_TOKEN' \\
  -H 'Content-Type: application/json' \\
  -d '{payload_json}'
""")

print("=" * 70)
print("Python Request Example")
print("=" * 70)

print(f"""
import aiohttp
import asyncio

async def get_presigned_urls():
    url = "https://api.fotosfolio.com/uploads/presigned-urls"

    headers = {{
        "accept": "application/json",
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    }}

    payload = {json.dumps(payload, indent=4)}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()

            # Response contains mapping of fileName to presigned URL
            presigned_urls = data.get("urls", data)

            for file_name, presigned_url in presigned_urls.items():
                print(f"File: {{file_name}}")
                print(f"URL: {{presigned_url}}\\n")

            return presigned_urls

# Run the async function
asyncio.run(get_presigned_urls())
""")

print("\n" + "=" * 70)
print("Request Body Structure")
print("=" * 70)

print("""
{
  "files": [
    {
      "fileName": "string (S3 object key)",
      "contentType": "string (MIME type)"
    }
  ]
}

Where:
- fileName: Full S3 object key (e.g., "Test2_xxx/ftp/camera1/file.jpg")
- contentType: MIME type of the file (e.g., "image/jpeg", "video/mp4")
""")

print("\n" + "=" * 70)
print("Expected Response Format")
print("=" * 70)

print("""
{
  "urls": {
    "Test2_xxx/ftp/camera1/file.jpg": "https://s3.amazonaws.com/...",
    "Test2_xxx/ftp/camera1/video.mp4": "https://s3.amazonaws.com/...",
    ...
  }
}

Or simply a flat object:
{
  "Test2_xxx/ftp/camera1/file.jpg": "https://s3.amazonaws.com/...",
  "Test2_xxx/ftp/camera1/video.mp4": "https://s3.amazonaws.com/...",
  ...
}
""")

print("\n" + "=" * 70)
print("Common Content Types")
print("=" * 70)

common_types = {
    "Images": {
        ".jpg, .jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff, .tif": "image/tiff",
    },
    "Videos": {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".wmv": "video/x-ms-wmv",
        ".flv": "video/x-flv",
        ".mkv": "video/x-matroska",
    },
    "Documents": {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".csv": "text/csv",
    },
    "Audio": {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
    },
}

for category, types in common_types.items():
    print(f"\n{category}:")
    for ext, mime in types.items():
        print(f"  {ext:20} -> {mime}")

print("\n" + "=" * 70)
print("Complete Workflow")
print("=" * 70)

print("""
Step 1: Validate Storage
  POST /storage/validate/{user_id}/{size_in_gb}
  Body: {"fileKeys": ["file1", "file2", ...]}
  Response: {"reservationId": "abc-123"}

  ✅ Store reservation ID safely for later use!

Step 2: Get Presigned URLs
  POST /uploads/presigned-urls
  Body: {"files": [{"fileName": "...", "contentType": "..."}]}
  Response: {"urls": {"file1": "url1", "file2": "url2"}}

Step 3: Upload Files to S3
  PUT {presigned_url}
  Body: (binary file data)

Step 4: Commit Storage
  POST /storage/commit/{reservation_id}
  Response: success confirmation

Step 5: Save Metadata
  POST /uploads/ftp/bulk/{userId}
  Body: {"files": [metadata objects]}
""")

print("\n" + "=" * 70)
print("Implementation in processor.py")
print("=" * 70)

print("""
The processor now:

1. Validates storage and gets reservation_id
   logger.info(f"✅ Reservation ID stored safely: {reservation_id}")

2. Prepares files info with fileName and contentType:
   files_info = [
       {"fileName": info["file_key"], "contentType": info["mime_type"]}
       for info in file_info_list
   ]

3. Requests presigned URLs:
   presigned_urls = await api_client.get_presigned_urls(files_info)

4. Uploads files using the presigned URLs

5. Commits using the stored reservation_id:
   await api_client.commit_storage(reservation_id)
""")

print("\n" + "=" * 70)
print("✅ All API calls now use the correct format!")
print("=" * 70)
