# API Workflow Documentation

Complete guide for the file upload workflow with storage validation, presigned URLs, and reservation ID tracking.

## Overview

The FTP server processes uploaded files through a multi-step workflow that involves:
1. **Storage Validation** - Reserve storage space and get reservation ID
2. **Presigned URLs** - Get secure upload URLs for S3
3. **File Upload** - Upload files to S3 using presigned URLs
4. **Storage Commit** - Finalize the storage reservation
5. **Metadata Save** - Store file metadata in the database

## Complete Workflow

### Step 1: Validate Storage and Get Reservation ID

**Endpoint:** `POST /storage/validate/{user_id}/{file_size_in_gb}`

**Purpose:** Reserve storage space and get a reservation ID for tracking the upload session.

**Request Format:**
```bash
curl -X 'POST' \
  'https://prod.fotosfolio.com/storage/validate/6905548a-b98e-4c33-a101-8f007499d8a1/0.1' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "fileKeys": [
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/file1.jpg",
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/file2.mp4",
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/file3.png"
  ]
}'
```

**Parameters:**
- `user_id`: User UUID (e.g., `6905548a-b98e-4c33-a101-8f007499d8a1`)
- `file_size_in_gb`: Total size of all files in GB (e.g., `0.1` for 100MB)

**Request Body:**
```json
{
  "fileKeys": [
    "string"
  ]
}
```

**File Key Format:**
```
{username_userid}/ftp/{ftp_username}/{filename}
```
- `username_userid`: e.g., `Test2_6905548a-b98e-4c33-a101-8f007499d8a1`
- `ftp_username`: Folder name (e.g., `camera1`, `camera2`, `uploads`)
- `filename`: File name with extension

**Response:**
```json
{
  "reservationId": "abc-123-def-456"
}
```

**⚠️ IMPORTANT:** Store the `reservationId` safely! It's required for Step 4 (Commit Storage).

**File Size Conversion:**
```python
# Convert bytes to GB
total_file_size_gb = total_file_size_bytes / (1024**3)
total_file_size_gb = round(total_file_size_gb, 6)
```

**Examples:**
- 100 MB = 104,857,600 bytes = 0.097656 GB
- 500 MB = 524,288,000 bytes = 0.488281 GB
- 1 GB = 1,073,741,824 bytes = 1.0 GB
- 2.5 GB = 2,684,354,560 bytes = 2.5 GB

---

### Step 2: Get Presigned URLs

**Endpoint:** `POST /uploads/presigned-urls`

**Purpose:** Get secure S3 presigned URLs for uploading each file.

**Request Format:**
```bash
curl -X 'POST' \
  'https://api.fotosfolio.com/uploads/presigned-urls' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "files": [
    {
      "fileName": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/image.jpg",
      "contentType": "image/jpeg"
    },
    {
      "fileName": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/video.mp4",
      "contentType": "video/mp4"
    }
  ]
}'
```

**Request Body:**
```json
{
  "files": [
    {
      "fileName": "string (S3 object key)",
      "contentType": "string (MIME type)"
    }
  ]
}
```

**Common Content Types:**

| File Extension | MIME Type |
|----------------|-----------|
| `.jpg`, `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.gif` | `image/gif` |
| `.webp` | `image/webp` |
| `.mp4` | `video/mp4` |
| `.mov` | `video/quicktime` |
| `.avi` | `video/x-msvideo` |
| `.pdf` | `application/pdf` |
| `.txt` | `text/plain` |
| `.mp3` | `audio/mpeg` |

**Response:**
```json
{
  "urls": {
    "Test2_xxx/ftp/camera1/image.jpg": "https://s3.amazonaws.com/bucket/...?signature=...",
    "Test2_xxx/ftp/camera1/video.mp4": "https://s3.amazonaws.com/bucket/...?signature=..."
  }
}
```

Or flat format:
```json
{
  "Test2_xxx/ftp/camera1/image.jpg": "https://s3.amazonaws.com/bucket/...?signature=...",
  "Test2_xxx/ftp/camera1/video.mp4": "https://s3.amazonaws.com/bucket/...?signature=..."
}
```

---

### Step 3: Upload Files to S3

**For each file, upload using its presigned URL:**

```bash
curl -X PUT \
  'https://s3.amazonaws.com/bucket/key?signature=...' \
  -H 'Content-Type: image/jpeg' \
  --data-binary '@/path/to/file.jpg'
```

**Important:**
- Use `PUT` method (not POST)
- Include the correct `Content-Type` header
- Upload the raw binary file data
- The presigned URL contains authentication, so no additional headers needed
- Each URL is temporary and expires after a set time

---

### Step 4: Commit Storage Reservation

**Endpoint:** `POST /storage/commit/{reservation_id}`

**Purpose:** Finalize the storage reservation after successful uploads.

**Request Format:**
```bash
curl -X 'POST' \
  'https://prod.fotosfolio.com/storage/commit/abc-123-def-456' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json'
```

**Parameters:**
- `reservation_id`: The reservation ID from Step 1 (MUST be stored safely!)

**Response:**
```json
{
  "success": true,
  "message": "Storage committed successfully"
}
```

**⚠️ CRITICAL:** This step confirms the upload and finalizes storage allocation. If this fails, the uploaded files may not be properly tracked.

---

### Step 5: Save File Metadata

**Endpoint:** `POST /uploads/ftp/bulk/{userId}`

**Purpose:** Save file metadata to the database.

**Request Format:**
```bash
curl -X 'POST' \
  'https://api.fotosfolio.com/uploads/ftp/bulk/{userId}' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "files": [
    {
      "fileId": "unique-file-id-1",
      "fileName": "image.jpg",
      "mime_type": "image/jpeg",
      "friendlyUrl": "https://s3.amazonaws.com/bucket/key",
      "downloadUrl": "https://s3.amazonaws.com/bucket/key",
      "nativeUrl": "https://s3.amazonaws.com/bucket/key",
      "s3Url": "https://s3.amazonaws.com/bucket/key",
      "folder": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1",
      "filesize": 1048576,
      "folderId": "",
      "userId": "6905548a-b98e-4c33-a101-8f007499d8a1",
      "projectId": ""
    }
  ]
}'
```

**Metadata Fields:**
- `fileId`: Unique identifier (UUID)
- `fileName`: Original file name
- `mime_type`: MIME type (e.g., `image/jpeg`)
- `friendlyUrl`, `downloadUrl`, `nativeUrl`, `s3Url`: S3 URL (without query parameters)
- `folder`: Folder path (e.g., `Test2_xxx/ftp/camera1`)
- `filesize`: File size in bytes
- `userId`: User UUID
- `folderId`, `projectId`: Optional IDs

---

## Implementation in Code

### Python Implementation

```python
import aiohttp

async def complete_upload_workflow():
    """Complete workflow example."""
    
    # Configuration
    user_id = "6905548a-b98e-4c33-a101-8f007499d8a1"
    files_info = [
        {
            "key": "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/image.jpg",
            "size": 1048576,  # bytes
            "content_type": "image/jpeg"
        }
    ]
    
    # Step 1: Validate Storage
    total_size_gb = sum(f["size"] for f in files_info) / (1024**3)
    total_size_gb = round(total_size_gb, 6)
    
    validate_url = f"https://prod.fotosfolio.com/storage/validate/{user_id}/{total_size_gb}"
    validate_payload = {"fileKeys": [f["key"] for f in files_info]}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(validate_url, json=validate_payload) as response:
            data = await response.json()
            reservation_id = data["reservationId"]
            print(f"✅ Reservation ID: {reservation_id}")
    
    # Step 2: Get Presigned URLs
    presigned_url = "https://api.fotosfolio.com/uploads/presigned-urls"
    presigned_payload = {
        "files": [
            {"fileName": f["key"], "contentType": f["content_type"]}
            for f in files_info
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(presigned_url, json=presigned_payload) as response:
            data = await response.json()
            presigned_urls = data.get("urls", data)
            print(f"✅ Got {len(presigned_urls)} presigned URLs")
    
    # Step 3: Upload Files to S3
    for file_info in files_info:
        file_key = file_info["key"]
        presigned_upload_url = presigned_urls[file_key]
        
        async with aiohttp.ClientSession() as session:
            with open("local_file.jpg", "rb") as f:
                async with session.put(presigned_upload_url, data=f) as response:
                    response.raise_for_status()
                    print(f"✅ Uploaded {file_key}")
    
    # Step 4: Commit Storage
    commit_url = f"https://prod.fotosfolio.com/storage/commit/{reservation_id}"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(commit_url) as response:
            response.raise_for_status()
            print(f"✅ Committed reservation {reservation_id}")
    
    # Step 5: Save Metadata
    metadata_url = f"https://api.fotosfolio.com/uploads/ftp/bulk/{user_id}"
    metadata_payload = {
        "files": [
            {
                "fileId": "generated-uuid",
                "fileName": "image.jpg",
                "mime_type": "image/jpeg",
                "s3Url": presigned_urls[file_info["key"]].split("?")[0],
                "folder": "Test2_xxx/ftp/camera1",
                "filesize": file_info["size"],
                "userId": user_id
            }
            for file_info in files_info
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(metadata_url, json=metadata_payload) as response:
            response.raise_for_status()
            print("✅ Metadata saved")
```

---

## Reservation ID Management

### Why Reservation ID is Critical

The reservation ID:
- Links the storage validation with the final commit
- Ensures atomicity of the upload operation
- Tracks storage quota usage
- Prevents orphaned uploads
- Enables rollback on failure

### Storage Best Practices

1. **Store Immediately:** Save reservation ID as soon as received from Step 1
2. **Log Safely:** Use structured logging with the reservation ID
3. **Track State:** Associate all files in batch with the same reservation ID
4. **Handle Failures:** Keep reservation ID even if uploads fail (for cleanup)
5. **Timeout Handling:** Reservation IDs may expire if not committed promptly

### Example Logging

```python
# Good: Structured logging with reservation ID
logger.info(f"✅ Reservation ID stored safely: {reservation_id}")
logger.info(f"Using stored reservation ID: {reservation_id}")
logger.info(f"✅ Successfully committed reservation: {reservation_id}")

# Track throughout the workflow
logger.error(f"Failed to commit reservation {reservation_id}: {error}")
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request on validate | File size in bytes instead of GB | Convert to GB: `size / (1024**3)` |
| 400 Bad Request on presigned | Wrong payload format | Use `{"files": [{"fileName": ..., "contentType": ...}]}` |
| 403 Forbidden | Invalid/expired token | Refresh authentication token |
| 404 on commit | Invalid reservation ID | Ensure reservation ID from Step 1 is used |
| Upload timeout | File too large | Increase timeout or use multipart upload |

### Retry Logic

```python
async def with_retry(func, max_retries=3):
    """Execute function with exponential backoff retry."""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt < max_retries:
                delay = 2 ** attempt  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s")
                await asyncio.sleep(delay)
            else:
                raise
```

---

## Testing

### Test Storage Validation
```bash
python test_validate_storage.py
```

### Test Presigned URLs
```bash
python test_presigned_urls.py
```

### Manual Testing with cURL

See examples in each step above, or use the test scripts for formatted output.

---

## Summary Checklist

- [ ] **Step 1:** Validate storage with file size in GB
- [ ] **Step 1:** Store reservation ID safely
- [ ] **Step 2:** Get presigned URLs with fileName and contentType
- [ ] **Step 3:** Upload files to S3 using PUT requests
- [ ] **Step 4:** Commit storage using stored reservation ID
- [ ] **Step 5:** Save metadata with file details
- [ ] **All Steps:** Include proper error handling and logging
- [ ] **All Steps:** Use correct authentication headers

---

## Additional Resources

- `api_client.py` - API client implementation
- `processor.py` - Batch processor implementation
- `storage_client.py` - S3 upload client
- `test_validate_storage.py` - Storage validation examples
- `test_presigned_urls.py` - Presigned URLs examples

---

**Last Updated:** 2024
**Status:** ✅ Production Ready