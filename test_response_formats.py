"""
Test script to demonstrate presigned URLs API response formats.
This helps understand what the API returns and how we handle it.
"""

import json

print("=" * 80)
print("Presigned URLs API - Response Format Analysis")
print("=" * 80)

# Example request
request_payload = {
    "files": [
        {
            "fileName": "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/image1.jpg",
            "contentType": "image/jpeg",
        },
        {
            "fileName": "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/video1.mp4",
            "contentType": "video/mp4",
        },
    ]
}

print("\n📤 REQUEST:")
print(json.dumps(request_payload, indent=2))

print("\n" + "=" * 80)
print("Possible Response Formats")
print("=" * 80)

# Format 1: List of objects with fileName and url
response_format_1 = [
    {
        "fileName": "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/image1.jpg",
        "url": "https://s3.amazonaws.com/bucket/path/image1.jpg?signature=abc123",
    },
    {
        "fileName": "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/video1.mp4",
        "url": "https://s3.amazonaws.com/bucket/path/video1.mp4?signature=def456",
    },
]

print("\n📥 FORMAT 1: List of Objects")
print("Response Type: list")
print(json.dumps(response_format_1, indent=2))
print("\nHandling Code:")
print("""
if isinstance(response, list):
    presigned_urls = {item["fileName"]: item["url"] for item in response}
""")
print("\nResult:")
result_1 = {item["fileName"]: item["url"] for item in response_format_1}
print(json.dumps(result_1, indent=2))

# Format 2: Object with 'urls' key containing dict
response_format_2 = {
    "urls": {
        "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/image1.jpg": "https://s3.amazonaws.com/bucket/path/image1.jpg?signature=abc123",
        "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/video1.mp4": "https://s3.amazonaws.com/bucket/path/video1.mp4?signature=def456",
    }
}

print("\n" + "-" * 80)
print("\n📥 FORMAT 2: Object with 'urls' key")
print("Response Type: dict")
print(json.dumps(response_format_2, indent=2))
print("\nHandling Code:")
print("""
if isinstance(response, dict):
    presigned_urls = response.get("urls", response)
""")
print("\nResult:")
result_2 = response_format_2.get("urls", response_format_2)
print(json.dumps(result_2, indent=2))

# Format 3: Flat object (direct mapping)
response_format_3 = {
    "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/image1.jpg": "https://s3.amazonaws.com/bucket/path/image1.jpg?signature=abc123",
    "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/video1.mp4": "https://s3.amazonaws.com/bucket/path/video1.mp4?signature=def456",
}

print("\n" + "-" * 80)
print("\n📥 FORMAT 3: Flat Object (Direct Mapping)")
print("Response Type: dict")
print(json.dumps(response_format_3, indent=2))
print("\nHandling Code:")
print("""
if isinstance(response, dict):
    presigned_urls = response.get("urls", response)
    # Since there's no 'urls' key, it returns the response itself
""")
print("\nResult:")
result_3 = response_format_3.get("urls", response_format_3)
print(json.dumps(result_3, indent=2))

print("\n" + "=" * 80)
print("Complete Response Handling Logic")
print("=" * 80)

handling_code = """
# Handle different response formats
if isinstance(response, list):
    # Format 1: List of objects with fileName and url
    presigned_urls = {item["fileName"]: item["url"] for item in response}
elif isinstance(response, dict):
    # Format 2 or 3: Dict with 'urls' key or flat dict
    presigned_urls = response.get("urls", response)
else:
    raise ValueError(f"Unexpected response format: {type(response)}")

if not isinstance(presigned_urls, dict):
    raise ValueError(f"Expected dict of presigned URLs, got: {type(presigned_urls)}")
"""

print(handling_code)

print("\n" + "=" * 80)
print("Testing Response Formats")
print("=" * 80)


def handle_response(response):
    """Handle different response formats."""
    if isinstance(response, list):
        # Format 1: List of objects with fileName and url
        presigned_urls = {item["fileName"]: item["url"] for item in response}
    elif isinstance(response, dict):
        # Format 2 or 3: Dict with 'urls' key or flat dict
        presigned_urls = response.get("urls", response)
    else:
        raise ValueError(f"Unexpected response format: {type(response)}")

    if not isinstance(presigned_urls, dict):
        raise ValueError(
            f"Expected dict of presigned URLs, got: {type(presigned_urls)}"
        )

    return presigned_urls


# Test all formats
test_responses = [
    ("Format 1 (List)", response_format_1),
    ("Format 2 (Dict with 'urls')", response_format_2),
    ("Format 3 (Flat Dict)", response_format_3),
]

for format_name, test_response in test_responses:
    print(f"\n✅ Testing {format_name}:")
    try:
        result = handle_response(test_response)
        print(f"   Success! Got {len(result)} URLs")
        for file_name in list(result.keys())[:1]:  # Show first one
            print(f"   Example: {file_name[:50]}... -> {result[file_name][:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("Current Error Analysis")
print("=" * 80)

print("""
Based on your log:
  'list' object has no attribute 'get'

This means the API is returning Format 1 (a list), but the old code was trying
to use .get() on it (which only works on dicts).

The updated code now handles all three formats correctly:
1. Checks if response is a list first
2. Converts list to dict using {item["fileName"]: item["url"]}
3. Falls back to dict handling for other formats

Files info sent:
[{
  'fileName': 'test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/images.jpg',
  'contentType': 'image/jpeg'
}]

✅ This is the correct format!
✅ The API should now work with the updated response handling
""")

print("\n" + "=" * 80)
print("Expected API Response (Format 1 - List)")
print("=" * 80)

expected_response = [
    {
        "fileName": "test_8df50935-1c78-4981-b885-f94c513fb02d/ftp/camera1/images.jpg",
        "url": "https://s3.amazonaws.com/bucket/path/images.jpg?signature=xyz789",
    }
]

print(json.dumps(expected_response, indent=2))

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

print("""
✅ The presigned URLs API returns a LIST of objects
✅ Each object has 'fileName' and 'url' keys
✅ The updated code converts this to a dict mapping
✅ The request format you're sending is correct

Next steps:
1. The code should now work correctly
2. Check logs for successful presigned URL retrieval
3. Files should upload to S3 successfully
""")
