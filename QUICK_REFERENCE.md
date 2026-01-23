# FTP File Processor - Quick Reference

## 🎯 What Does It Do?

Watches your FTP server and automatically uploads files to S3 through your backend API.

```
Camera → FTP Server → [This App] → Backend API → S3
                         ↓
                    Watches files
                    Batches uploads
                    Deletes after success
```

---

## 📁 Required Directory Structure

```
/ftp_root/
└── username_userid/        # Format: name_id (e.g., john_123)
    └── ftp/                # Must be exactly "ftp"
        └── camera1/        # Any name for camera/device
            └── files...
```

**Multiple Users/Cameras:**
```
/ftp_root/
├── john_123/ftp/camera1/
├── john_123/ftp/camera2/
├── jane_456/ftp/camera1/
└── bob_789/ftp/front_cam/
```

---

## ⚙️ Essential Configuration

### .env File (Minimum Required)

```bash
# REQUIRED
API_BASE_URL=https://prod.fotosfolio.com
API_AUTH_TOKEN=your_actual_bearer_token

# REQUIRED - Point to your FTP directory
FTP_ROOT_DIR=/var/ftp/uploads

# OPTIONAL (defaults shown)
BATCH_SIZE=10
MAX_CONCURRENT_UPLOADS=4
BATCH_TIMEOUT_SECONDS=30
```

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
nano .env  # Set API_AUTH_TOKEN and FTP_ROOT_DIR

# 3. Run
python main.py
```

---

## 📊 How It Works

1. **Detects** - Watches for new files in FTP directories
2. **Batches** - Groups up to 10 files (or waits 30 seconds)
3. **Validates** - Checks storage quota via API
4. **Gets URLs** - Backend generates presigned S3 URLs
5. **Uploads** - Direct upload to S3 (4 parallel streams)
6. **Commits** - Notifies backend of successful uploads
7. **Cleans** - Deletes files from FTP server

---

## 🔍 Monitoring Commands

```bash
# Watch live logs
tail -f ftp_processor.log

# Search for errors
grep ERROR ftp_processor.log

# Count successful uploads today
grep "Upload completed:" ftp_processor.log | grep "$(date +%Y-%m-%d)" | wc -l

# View configuration
python -c "from config import Config; print(Config.display())"
```

---

## ⚡ Performance Tuning

### High Volume (Many files)
```bash
BATCH_SIZE=20
MAX_CONCURRENT_UPLOADS=8
BATCH_TIMEOUT_SECONDS=15
```

### Low Volume (Few files)
```bash
BATCH_SIZE=5
MAX_CONCURRENT_UPLOADS=2
BATCH_TIMEOUT_SECONDS=60
```

### Slow Network
```bash
MAX_RETRIES=5
RETRY_INITIAL_DELAY=2
API_TIMEOUT=60
```

---

## 🐛 Quick Troubleshooting

| Symptom | Quick Fix |
|---------|-----------|
| "FTP_ROOT_DIR does not exist" | Set `FTP_ROOT_DIR=/actual/path` in .env |
| "No valid files in batch" | Check path: `username_123/ftp/camera1/file.jpg` |
| "API_AUTH_TOKEN is required" | Add token to .env file |
| "Storage validation failed" | Verify API token is correct |
| Files not detected | Wait for upload to complete, check permissions |
| "Upload failed after retries" | Check S3 connectivity, increase MAX_RETRIES |

---

## 📝 Log Messages Explained

```
✅ "File upload detected" - File found, added to batch
✅ "Batch full" - Processing 10 files immediately
✅ "Batch timeout reached" - Processing partial batch
✅ "Storage validated successfully" - API approved upload
✅ "Upload completed" - File uploaded to S3
✅ "Batch processing completed" - All done, files deleted

⚠️  "Ignoring file with invalid path" - Wrong directory structure
⚠️  "No presigned URL for file" - API didn't provide URL
⚠️  "Upload failed (attempt X/Y)" - Retrying upload

❌ "Storage validation failed" - API rejected (quota/auth issue)
❌ "Upload failed after X attempts" - Gave up after retries
❌ "Failed to save metadata" - Backend didn't accept metadata
```

---

## 🔐 Security Checklist

- [ ] `.env` file has `chmod 600` permissions
- [ ] `.env` is in `.gitignore`
- [ ] API token has minimal required permissions
- [ ] FTP directory is READ-ONLY for processor
- [ ] Processor runs as dedicated user (not root)
- [ ] Logs don't contain sensitive data

---

## 📞 When Things Go Wrong

### Step 1: Check Configuration
```bash
python -c "from config import Config; Config.validate()"
```

### Step 2: Enable Debug Logging
```bash
# In .env
LOG_LEVEL=DEBUG
```

### Step 3: Test Directory Structure
```bash
tree /var/ftp/uploads -L 4
```

### Step 4: Test API Connection
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://prod.fotosfolio.com/storage/validate/123/1000
```

### Step 5: Check Last 50 Log Lines
```bash
tail -50 ftp_processor.log
```

---

## 🔄 Common Operations

### Restart Service
```bash
# Systemd
sudo systemctl restart ftp-processor

# Docker
docker-compose restart file-processor

# Direct
# Ctrl+C then: python main.py
```

### View Live Activity
```bash
# Real-time logs
tail -f ftp_processor.log

# Docker logs
docker-compose logs -f file-processor

# Systemd logs
sudo journalctl -u ftp-processor -f
```

### Clear Old Logs
```bash
# Rotate logs manually
mv ftp_processor.log ftp_processor.log.old

# Or let it rotate automatically (10MB max)
```

---

## 📚 Full Documentation

- **Complete Setup**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Architecture**: See [README.md](README.md)
- **Source Code**: Browse `*.py` files

---

## 🎓 Key Concepts

**Batch Processing**
- Groups files to reduce API calls
- Max 10 files per batch (configurable)
- 30 second timeout (configurable)

**Presigned URLs**
- Backend generates temporary S3 upload URLs
- Direct upload (no data through backend)
- More efficient than proxy uploads

**Event-Driven**
- Uses file system events (inotify)
- No CPU-intensive polling
- Instant detection when file closes

**Streaming Upload**
- Reads file in chunks (1MB default)
- Low memory usage
- Handles large files efficiently

**Parallel Uploads**
- Up to 4 concurrent S3 uploads
- Controlled by semaphore
- Faster batch processing

---

## 💡 Pro Tips

✅ Start with default settings, tune later
✅ Monitor first batch carefully  
✅ Keep `BATCH_SIZE` × `file_size` reasonable
✅ Higher `MAX_CONCURRENT_UPLOADS` ≠ always faster
✅ Enable DEBUG logging for first test
✅ Set LOG_LEVEL=INFO for production
✅ Backup logs before rotation
✅ Monitor disk space in FTP directory

---

## 📊 Expected Performance

| File Size | Batch Size | Processing Time | Throughput |
|-----------|------------|-----------------|------------|
| 2 MB      | 10 files   | 5-10 seconds    | 2-4 MB/s   |
| 10 MB     | 10 files   | 20-30 seconds   | 3-5 MB/s   |
| Mixed     | 10 files   | 10-20 seconds   | 3-4 MB/s   |

*Network dependent - your mileage may vary*

---

**Questions? Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed help!**