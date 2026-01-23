#!/usr/bin/env python3
"""
Test script to demonstrate proper JSON formatting with double quotes.
This shows how Python's print() uses single quotes but json.dumps() uses proper JSON format.
"""

import json

# Sample metadata list (similar to what processor.py generates)
metadata_list = [
    {
        "fileId": "0bd648e8-9bf2-4d9d-805e-8b66024d7c4e",
        "fileName": "1756038748277_Otaku_Jatra_2.mov",
        "mime_type": "video/quicktime",
        "friendlyUrl": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1756038748277_Otaku_Jatra_2.mov",
        "downloadUrl": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1756038748277_Otaku_Jatra_2.mov",
        "nativeUrl": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1756038748277_Otaku_Jatra_2.mov",
        "s3Url": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1756038748277_Otaku_Jatra_2.mov",
        "folder": "alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest",
        "filesize": 0.03582763671875,
        "folderId": "ftp",
        "userId": "66b59d64-8d1d-4627-a5e7-dd4a02213245",
        "projectId": "ftp",
    },
    {
        "fileId": "e0f5d089-7951-4b85-9c35-5af21421a4bc",
        "fileName": "1760096778395.jpg",
        "mime_type": "image/jpeg",
        "friendlyUrl": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1760096778395.jpg",
        "downloadUrl": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1760096778395.jpg",
        "nativeUrl": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1760096778395.jpg",
        "s3Url": "https://cdn.fotosfolio.com/alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest/1760096778395.jpg",
        "folder": "alphatester_66b59d64-8d1d-4627-a5e7-dd4a02213245/ftp/aresTest",
        "filesize": 0.004471134394407272,
        "folderId": "ftp",
        "userId": "66b59d64-8d1d-4627-a5e7-dd4a02213245",
        "projectId": "ftp",
    },
]

print("=" * 80)
print("WRONG WAY - Using print() directly (shows single quotes):")
print("=" * 80)
print(metadata_list)
print()

print("=" * 80)
print("CORRECT WAY - Using json.dumps() (shows double quotes - valid JSON):")
print("=" * 80)
print(json.dumps(metadata_list, indent=2))
print()

print("=" * 80)
print("Compact JSON (without indentation):")
print("=" * 80)
print(json.dumps(metadata_list))
print()

print("=" * 80)
print("IMPORTANT NOTE:")
print("=" * 80)
print("When using aiohttp with json=payload, it automatically converts to proper JSON")
print("with double quotes. The single quotes you see are just Python's representation.")
print()
print("In processor.py, we now use:")
print("  logger.info(f'Metadata: {json.dumps(metadata_list, indent=2)}')")
print()
print("In api_client.py, when we do:")
print("  await self.session.post(url, json=payload)")
print()
print("The 'json=' parameter automatically serializes with double quotes!")
