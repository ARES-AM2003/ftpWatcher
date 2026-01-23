# FTP File Processor - Complete Setup Guide

## 📋 Overview

This application watches your FTP server directories and automatically uploads files to object storage (S3) through your backend API using presigned URLs.

### How It Works

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Cameras   │─FTP─>│ FTP Server  │      │   Backend   │      │     S3      │
│             │      │  (Existing) │      │     API     │      │   Storage   │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                            │                     │                     │
                            │ watch               │                     │
                            ▼                     │                     │
                     ┌─────────────┐              │                     │
                     │    File     │──validate───>│                     │
                     │  Processor  │<─presigned───┘                     │
                     │ (This App)  │──────upload──────────────────────>│
                     └─────────────┘<─────commit/metadata──────────────┘
```

### Processing Flow

1. **Camera uploads** file to FTP → `/ftp_root/john_123/ftp/camera1/IMG_001.jpg`
2. **Watcher detects** file upload completion
3. **Batching** collects up to 10 files (or 30s timeout)
4. **Backend API** validates storage quota
5. **Backend API** generates presigned S3 URLs
6. **Processor uploads** directly to S3 (parallel, streaming)
7. **Backend API** commits storage reservation
8. **Backend API** receives file metadata
9. **Processor deletes** file from FTP server

---

## 🗂️ Required Directory Structure

Your FTP server must follow this structure:

```
/ftp_root/                          # Root FTP directory
└── username_userid/                # User folder (e.g., john_123)
    └── ftp/                        # Fixed "ftp" folder
        ├── camera1/                # Camera/device folders
        │   ├── IMG_001.jpg
        │   ├── IMG_002.jpg
        │   └── VID_001.mp4
        ├── camera2/
        │   ├── IMG_001.jpg
        │   └── IMG_002.jpg
        └── camera3/
            └── IMG_001.jpg
```

### Important Notes:
- **Multiple users**: Create multiple `username_userid` folders (e.g., `john_123`, `jane_456`)
- **Multiple cameras**: Each user can have multiple camera folders
- **Naming convention**: User folder MUST be `username_userid` format (underscore separates name and ID)
- **"ftp" folder**: This middle folder is required in the path structure
- **Camera folders**: Name them as you like (camera1, camera2, cam_front, etc.)

---

## 🚀 Setup Instructions

### Step 1: Prerequisites

✅ **FTP Server** - Already running on your server  
✅ **Python 3.11+** - Required for the processor  
✅ **Backend API** - With presigned URL support  
✅ **Internet Access** - For processor to reach API and S3

### Step 2: Clone and Install

```bash
# Navigate to your project directory
cd /home/ares/Projects/BNT/ftpserver

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Configuration:**

```bash
# ========================================
# API Configuration (REQUIRED)
# ========================================
API_BASE_URL=https://prod.fotosfolio.com
API_AUTH_TOKEN=your_actual_bearer_token_here
API_TIMEOUT=30

# ========================================
# S3 Configuration (OPTIONAL)
# ========================================
# Bucket name may be needed for API requests (check your backend)
S3_BUCKET_NAME=your-bucket-name

# ========================================
# FTP Configuration (REQUIRED)
# ========================================
# Point to your actual FTP root directory
FTP_ROOT_DIR=/var/ftp/uploads
# Or wherever your FTP server stores uploads

# ========================================
# Processing Configuration
# ========================================
BATCH_SIZE=10                    # Process 10 files at a time
MAX_CONCURRENT_UPLOADS=4         # 4 parallel uploads to S3
BATCH_TIMEOUT_SECONDS=30         # Wait max 30s for batch to fill

# ========================================
# Retry Configuration
# ========================================
MAX_RETRIES=3                    # Retry failed operations 3 times
RETRY_BACKOFF_MULTIPLIER=2       # Exponential backoff (1s, 2s, 4s)
RETRY_INITIAL_DELAY=1            # Start with 1 second delay

# ========================================
# Upload Configuration
# ========================================
UPLOAD_CHUNK_SIZE=1048576        # 1MB chunks for streaming

# ========================================
# Logging Configuration
# ========================================
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=ftp_processor.log
LOG_MAX_BYTES=10485760          # 10MB per log file
LOG_BACKUP_COUNT=5              # Keep 5 old log files
```

### Step 4: Verify FTP Directory Structure

```bash
# Check your FTP directory exists
ls -la /var/ftp/uploads/

# Create test structure (if needed)
sudo mkdir -p /var/ftp/uploads/testuser_123/ftp/camera1
sudo chown -R ftp:ftp /var/ftp/uploads/  # Adjust ownership as needed

# Verify permissions (processor needs READ access)
ls -la /var/ftp/uploads/testuser_123/ftp/camera1/
```

### Step 5: Test Configuration

```bash
# Test configuration validity
python -c "from config import Config; Config.validate(); print('✅ Configuration valid!')"
```

---

## 🏃 Running the Processor

### Option 1: Run Directly (Development/Testing)

```bash
# Activate virtual environment
source venv/bin/activate

# Run processor
python main.py
```

**Expected Output:**
```
================================================================================
FTP Upload Processor Starting
================================================================================

Configuration:
  API Base URL: https://prod.fotosfolio.com
  API Auth Token: ********************
  API Timeout: 30s
  
  S3 Bucket: your-bucket-name
  Note: Using presigned URLs from backend API (no direct S3 credentials)
  
  FTP Root Dir: /var/ftp/uploads
  
  Batch Size: 10
  Max Concurrent Uploads: 4
  Batch Timeout: 30s
  
  Max Retries: 3
  Retry Backoff: 2.0x
  Initial Delay: 1.0s
  
  Upload Chunk Size: 1.0MB
  
  Log Level: INFO
  Log File: ftp_processor.log

Application started successfully
Monitoring FTP directories for new uploads...
File watcher started, monitoring: /var/ftp/uploads
```

### Option 2: Run with Docker

**Edit docker-compose.yml:**

```yaml
services:
  file-processor:
    build: .
    container_name: ftp-file-processor
    env_file:
      - .env
    environment:
      - FTP_ROOT_DIR=/ftp_root
    volumes:
      # CHANGE THIS: Point to your actual FTP directory
      - /var/ftp/uploads:/ftp_root:ro  # ← Update this path!
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - processor-network

networks:
  processor-network:
    driver: bridge
```

**Run with Docker:**

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f file-processor

# Stop
docker-compose down
```

### Option 3: Run as Systemd Service (Production)

**Create service file:**

```bash
sudo nano /etc/systemd/system/ftp-processor.service
```

**Service content:**

```ini
[Unit]
Description=FTP File Processor
After=network.target vsftpd.service

[Service]
Type=simple
User=ftpprocessor
Group=ftpprocessor
WorkingDirectory=/home/ares/Projects/BNT/ftpserver
Environment="PATH=/home/ares/Projects/BNT/ftpserver/venv/bin"
ExecStart=/home/ares/Projects/BNT/ftpserver/venv/bin/python main.py
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/ftp-processor/stdout.log
StandardError=append:/var/log/ftp-processor/stderr.log

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
# Create log directory
sudo mkdir -p /var/log/ftp-processor
sudo chown ftpprocessor:ftpprocessor /var/log/ftp-processor

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable ftp-processor

# Start service
sudo systemctl start ftp-processor

# Check status
sudo systemctl status ftp-processor

# View logs
sudo journalctl -u ftp-processor -f
```

---

## 🧪 Testing

### Test 1: Upload a File

```bash
# Upload via FTP (using any FTP client)
# Or manually place a file:
sudo cp ~/test.jpg /var/ftp/uploads/testuser_123/ftp/camera1/
```

**Watch processor logs:**
```bash
tail -f ftp_processor.log
```

**Expected log output:**
```
INFO - File upload detected: test.jpg (user: testuser_123, batch: 123)
INFO - Processing batch of 1 files
INFO - Batch summary: 1 files, total size: 2.50 MB
INFO - Validating storage for user 123: 2621440 bytes, 1 files
INFO - Storage validated successfully. Reservation ID: abc-123-def
INFO - Requesting presigned URLs for 1 files
INFO - Received 1 presigned URLs
INFO - Starting upload: test.jpg (2.50 MB)
INFO - Upload completed: test.jpg
INFO - Upload results: 1 successful, 0 failed
INFO - Committing storage reservation: abc-123-def
INFO - Storage committed successfully: abc-123-def
INFO - Saving metadata for 1 files
INFO - Metadata saved successfully for 1 files
INFO - Deleted file: /var/ftp/uploads/testuser_123/ftp/camera1/test.jpg
INFO - Batch processing completed: 1 files uploaded and cleaned up
```

### Test 2: Batch Upload

```bash
# Upload 15 files
for i in {1..15}; do
    sudo cp ~/test.jpg /var/ftp/uploads/testuser_123/ftp/camera1/test_$i.jpg
    sleep 1
done
```

**Expected behavior:**
- First batch of 10 files processes immediately
- Remaining 5 files wait for timeout (30s) or more files
- Or processes immediately if batch fills up

---

## 📊 Monitoring

### Check Logs

```bash
# Real-time logs
tail -f ftp_processor.log

# Search for errors
grep ERROR ftp_processor.log

# Search for specific user
grep "user: john_123" ftp_processor.log

# View last 100 lines
tail -n 100 ftp_processor.log
```

### Log Levels

- **DEBUG**: Detailed upload progress, chunk uploads
- **INFO**: File detection, batch processing, API calls
- **WARNING**: Invalid paths, missing URLs, retries
- **ERROR**: Upload failures, API errors
- **CRITICAL**: System-level failures

### Metrics to Monitor

```bash
# Count successful uploads
grep "Upload completed:" ftp_processor.log | wc -l

# Count failed uploads
grep "Upload failed after" ftp_processor.log | wc -l

# Count batches processed
grep "Batch processing completed:" ftp_processor.log | wc -l

# Find average batch size
grep "Batch summary:" ftp_processor.log | tail -20
```

---

## 🔧 Troubleshooting

### Problem: "FTP_ROOT_DIR does not exist"

**Solution:**
```bash
# Create the directory
sudo mkdir -p /var/ftp/uploads

# Set permissions (processor needs READ access)
sudo chmod 755 /var/ftp/uploads

# Update .env with correct path
nano .env
# Set: FTP_ROOT_DIR=/var/ftp/uploads
```

### Problem: "No valid files in batch"

**Cause:** File path doesn't match expected structure

**Solution:**
```bash
# Check current structure
tree /var/ftp/uploads

# Expected structure:
# /var/ftp/uploads/username_123/ftp/camera1/file.jpg
#                  └─────┬─────┘  │   └──┬──┘
#                   required    required  any name
```

### Problem: "Storage validation failed"

**Causes:**
- Invalid `API_AUTH_TOKEN`
- Backend API is down
- User quota exceeded
- Network connectivity issues

**Solution:**
```bash
# Test API connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://prod.fotosfolio.com/storage/validate/123/1000

# Check token in .env
cat .env | grep API_AUTH_TOKEN

# Check logs for specific error
grep "Storage validation failed" ftp_processor.log -A 5
```

### Problem: "Upload failed after 3 attempts"

**Causes:**
- Invalid presigned URL
- Network timeout
- S3 connectivity issues

**Solution:**
```bash
# Check if presigned URLs are valid
grep "presigned URL" ftp_processor.log

# Test S3 connectivity
curl -I https://s3.amazonaws.com

# Increase retry count in .env
MAX_RETRIES=5
RETRY_INITIAL_DELAY=2
```

### Problem: Files not being detected

**Causes:**
- Watcher not monitoring correct directory
- Permissions issue
- Files still being uploaded (not closed)

**Solution:**
```bash
# Verify watcher is running
grep "File watcher started" ftp_processor.log

# Check directory path
grep "monitoring:" ftp_processor.log

# Manually trigger by closing file
touch /var/ftp/uploads/testuser_123/ftp/camera1/test.jpg

# Check file permissions
ls -la /var/ftp/uploads/testuser_123/ftp/camera1/
```

---

## ⚙️ Configuration Tuning

### High Volume (Many cameras, frequent uploads)

```bash
BATCH_SIZE=20                    # Larger batches
MAX_CONCURRENT_UPLOADS=8         # More parallel uploads
BATCH_TIMEOUT_SECONDS=15         # Process faster
UPLOAD_CHUNK_SIZE=2097152        # 2MB chunks
```

### Low Volume (Few cameras, occasional uploads)

```bash
BATCH_SIZE=5                     # Smaller batches
MAX_CONCURRENT_UPLOADS=2         # Fewer parallel uploads
BATCH_TIMEOUT_SECONDS=60         # Wait longer for batches
UPLOAD_CHUNK_SIZE=524288         # 512KB chunks
```

### Slow Network

```bash
MAX_RETRIES=5                    # More retries
RETRY_INITIAL_DELAY=2            # Longer initial delay
API_TIMEOUT=60                   # Longer API timeout
UPLOAD_CHUNK_SIZE=524288         # Smaller chunks
```

### Fast Network

```bash
MAX_CONCURRENT_UPLOADS=10        # More parallel uploads
UPLOAD_CHUNK_SIZE=5242880        # 5MB chunks
BATCH_TIMEOUT_SECONDS=10         # Process quickly
```

---

## 🔒 Security Considerations

### File Permissions

```bash
# Processor needs READ-ONLY access
sudo chmod 755 /var/ftp/uploads
sudo chmod -R 644 /var/ftp/uploads/*/ftp/*/*.jpg

# Run as dedicated user
sudo useradd -r -s /bin/false ftpprocessor
sudo chown -R ftpprocessor:ftpprocessor /home/ares/Projects/BNT/ftpserver
```

### Environment Variables

```bash
# Protect .env file
chmod 600 .env

# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets manager in production
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### API Token

- Rotate tokens regularly
- Use token with minimal required permissions
- Monitor token usage in backend API logs

---

## 📈 Performance

### Current Optimizations

✅ **Event-driven** - Uses inotify (no polling)  
✅ **Streaming I/O** - No full files in memory  
✅ **Parallel uploads** - Up to 4/8/10 concurrent  
✅ **Batching** - Reduces API calls  
✅ **Async I/O** - Non-blocking operations  
✅ **Connection reuse** - HTTP keep-alive  

### Expected Performance

| Scenario | Files/Batch | Upload Time | Throughput |
|----------|-------------|-------------|------------|
| Small images (2MB) | 10 | ~5-10s | ~2-4 MB/s |
| Large images (10MB) | 10 | ~20-30s | ~3-5 MB/s |
| Mixed files | 10 | ~10-20s | ~3-4 MB/s |
| High volume (100 files) | 10 batches | ~2-5 min | ~3-4 MB/s |

*Actual performance depends on network speed, S3 region, file sizes*

---

## 🆘 Support

### Get Help

1. **Check logs**: `tail -f ftp_processor.log`
2. **Enable debug**: Set `LOG_LEVEL=DEBUG` in `.env`
3. **Test configuration**: `python -c "from config import Config; Config.validate()"`
4. **Check GitHub issues**: Look for similar problems

### Report Issues

Include:
- Configuration (hide secrets!)
- Log excerpt (last 50 lines)
- FTP directory structure
- Python version: `python --version`
- OS version: `uname -a`

---

## 📝 License

MIT License - See LICENSE file for details