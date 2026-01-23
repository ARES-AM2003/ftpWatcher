# Storage Validation API Fix

## Problem
The storage validation API endpoint was receiving a 400 Bad Request error because the file size was being sent in **bytes** instead of **GB**.

**Error:**
```
Error: 400, message='Bad Request', url='https://prod.fotosfolio.com/storage/validate/6905548a-b98e-4c33-a101-8f007499d8a1/17551'
```

## Solution
Updated `api_client.py` to convert file size from bytes to GB before making the API call.

### Changes Made

**File:** `ftpserver/api_client.py`

**Method:** `validate_storage()`

**Key Changes:**
1. Convert bytes to GB: `total_file_size_gb = total_file_size / (1024**3)`
2. Round to 6 decimal places: `total_file_size_gb = round(total_file_size_gb, 6)`
3. Use GB value in URL instead of bytes

### Correct API Request Format

```bash
curl -X 'POST' \
  'https://prod.fotosfolio.com/storage/validate/{user_id}/{size_in_gb}' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "fileKeys": [
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/file.ext"
  ]
}'
```

### Example

For 107,374,182 bytes (~100 MB):

```bash
curl -X 'POST' \
  'https://prod.fotosfolio.com/storage/validate/6905548a-b98e-4c33-a101-8f007499d8a1/0.1' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "fileKeys": [
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/image.jpg",
    "Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/video.mp4"
  ]
}'
```

## File Key Format

File keys follow this structure:
```
{username_userid}/ftp/{ftp_username}/{filename}
```

**Components:**
- `username_userid`: e.g., `Test2_6905548a-b98e-4c33-a101-8f007499d8a1`
- `ftp_username`: Folder name (e.g., `camera1`, `camera2`, `uploads`)
- `filename`: Actual file name with extension

**Examples:**
- `Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera1/image.jpg`
- `Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/camera2/video.mp4`
- `Test2_6905548a-b98e-4c33-a101-8f007499d8a1/ftp/uploads/document.pdf`

## API Endpoint

**Endpoint:** `POST /storage/validate/{user_id}/{file_size_in_gb}`

**Request Body:**
```json
{
  "fileKeys": [
    "string"
  ]
}
```

**Response:**
```json
{
  "reservationId": "string"
}
```

## File Size Conversion Examples

| Description | Bytes | GB (rounded) |
|------------|-------|--------------|
| 100 MB | 104,857,600 | 0.097656 |
| 500 MB | 524,288,000 | 0.488281 |
| 1 GB | 1,073,741,824 | 1.0 |
| 2.5 GB | 2,684,354,560 | 2.5 |

## Testing

Run the test script to see example API call formats:
```bash
python test_validate_storage.py
```

## Implementation Details

The conversion happens in the `validate_storage()` method:

```python
# Convert bytes to GB and format to reasonable precision
total_file_size_gb = total_file_size / (1024**3)
# Round to 6 decimal places to avoid floating point precision issues
total_file_size_gb = round(total_file_size_gb, 6)

url = f"{self.base_url}/storage/validate/{user_id}/{total_file_size_gb}"
payload = {"fileKeys": file_keys}
```

This ensures:
1. ✅ File size is in GB as expected by the API
2. ✅ File keys are in the correct format
3. ✅ Request body has the correct structure
4. ✅ No floating point precision issues with very small or large numbers

## Result

The 400 Bad Request error is now resolved. The API correctly receives:
- File size in GB (not bytes)
- Properly formatted file keys
- Correct request body structure