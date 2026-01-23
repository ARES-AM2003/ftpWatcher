# FTP Upload System

High-performance, disk, RAM, and CPU-optimized system for uploading files from cameras to an FTP server and then to object storage with backend API interactions using presigned URLs.

> 📖 **For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

## 🚀 Quick Start

### Prerequisites
- ✅ **FTP Server** already running on your server
- ✅ **Python 3.11+** installed
- ✅ **Backend API** with presigned URL support

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# 3. Update FTP_ROOT_DIR to point to your FTP directory
# Example: FTP_ROOT_DIR=/var/ftp/uploads

# 4. Add your API token
# API_AUTH_TOKEN=your_actual_token_here

# 5. Run the processor
python main.py
```

### FTP Directory Structure Required

```
/ftp_root/
└── username_userid/              # e.g., "john_123"
    └── ftp/
        ├── camera1/              # One camera per folder
        │   ├── IMG_001.jpg
        │   ├── IMG_002.jpg
        │   └── VID_001.mp4
        ├── camera2/
        │   └── IMG_001.jpg
        └── camera3/
            └── IMG_001.jpg
```

**Important:** Multiple users and cameras are supported automatically!

---

## Features

- **Event-Driven File Watching**: Uses inotify for minimal CPU usage
- **Batch Processing**: Processes files in batches of 10 with timeout
- **Parallel Uploads**: Up to 4 concurrent uploads to object storage
- **Streaming I/O**: Minimizes memory usage with chunked uploads
- **Retry Logic**: Exponential backoff for failed operations
- **Chroot Isolation**: Secure FTP server with user isolation
- **Modular Architecture**: Separate components for watching, processing, API, and storage

## Architecture

```
Cameras → FTP Server (chrooted) → File Watcher → Batch Processor → Object Storage
                                         ↓
                                   Backend API
```

## Directory Structure

```
ftpserver/
├── main.py              # Application entry point
├── config.py            # Configuration management
├── logger.py            # Logging configuration
├── utils.py             # Utility functions
├── watcher.py           # File watcher (inotify)
├── processor.py         # Batch processor
├── api_client.py        # Backend API client
├── storage_client.py    # S3 storage client
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── Dockerfile           # Container image
├── docker-compose.yml   # Multi-service orchestration
└── setup/
    ├── vsftpd.conf      # FTP server configuration
    └── setup_ftp.sh     # FTP server setup script
```

## Installation

### Prerequisites

✅ Python 3.11+  
✅ **Your existing FTP server** (vsftpd, ProFTPD, etc.)  
✅ Backend API with presigned URL support  

> **Note:** FTP server setup is separate from this processor. This application only watches and processes uploaded files.

### Setup

> 📖 **See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete instructions**

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Set FTP directory path**:
   ```bash
   # In .env file, point to your existing FTP directory
   FTP_ROOT_DIR=/var/ftp/uploads
   ```

4. **Add API credentials**:
   ```bash
   # In .env file
   API_AUTH_TOKEN=your_actual_bearer_token
   ```

5. **Run**:
   ```bash
   python main.py
   ```

## Configuration

Edit `.env` file with your settings:

```bash
# API Configuration (REQUIRED)
API_BASE_URL=https://prod.fotosfolio.com
API_AUTH_TOKEN=your_bearer_token_here

# S3 Configuration (Optional - may be needed for API requests)
S3_BUCKET_NAME=your-bucket-name
# Note: S3 credentials NOT needed - uploads use presigned URLs from backend API

# FTP Configuration (REQUIRED)
# Point this to your existing FTP server's upload directory
FTP_ROOT_DIR=/var/ftp/uploads

# Processing Configuration
BATCH_SIZE=10
MAX_CONCURRENT_UPLOADS=4
```

## Usage

### Running Locally (Development)

```bash
# With virtual environment
source venv/bin/activate
python main.py
```

### Running with Docker

**First, edit `docker-compose.yml` to point to your FTP directory:**

```yaml
volumes:
  - /var/ftp/uploads:/ftp_root:ro  # Update this path!
  - ./logs:/app/logs
```

**Then run:**

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f file-processor

# Stop
docker-compose down
```

### Running as Service (Production)

See [SETUP_GUIDE.md](SETUP_GUIDE.md#option-3-run-as-systemd-service-production) for systemd service setup.

## FTP Directory Structure

### Required Structure

```
/ftp_root/                          # Your FTP root (configure in .env)
└── username_userid/                # User folder: username_userid format
    └── ftp/                        # Fixed "ftp" folder (required)
        ├── camera1/                # Camera folders (any name)
        │   ├── IMG_001.jpg
        │   ├── IMG_002.jpg
        │   └── VID_001.mp4
        ├── camera2/
        │   └── IMG_001.jpg
        └── camera3/
            └── IMG_001.jpg
```

### Examples

**Single User, Single Camera:**
```
/var/ftp/uploads/john_123/ftp/camera1/
```

**Single User, Multiple Cameras:**
```
/var/ftp/uploads/john_123/ftp/camera1/
/var/ftp/uploads/john_123/ftp/camera2/
/var/ftp/uploads/john_123/ftp/camera3/
```

**Multiple Users, Multiple Cameras:**
```
/var/ftp/uploads/john_123/ftp/camera1/
/var/ftp/uploads/john_123/ftp/camera2/
/var/ftp/uploads/jane_456/ftp/camera1/
/var/ftp/uploads/jane_456/ftp/camera2/
```

### Important Rules

✅ User folder MUST be `username_userid` format (underscore separator)  
✅ Must have `/ftp/` folder in the path  
✅ Camera folders can have any name  
✅ Processor watches ALL folders automatically  
✅ Files are batched per user (not per camera)

## Processing Flow

1. **File Upload**: Camera uploads files to FTP server
2. **Detection**: File watcher detects new files
3. **Batching**: Files are batched (10 files or timeout)
4. **Validation**: Backend API validates storage availability
5. **Presigned URLs**: Backend API generates presigned S3 URLs
6. **Upload**: Direct parallel upload to S3 using presigned URLs (max 4 concurrent)
7. **Commit**: Commit storage reservation to backend
8. **Metadata**: Save file metadata to backend
9. **Cleanup**: Delete files from FTP server

## Performance Optimizations

### Disk
- Streaming I/O (no temporary files)
- Immediate cleanup after upload
- Chunked reading (1MB chunks)

### RAM
- Streaming uploads (no full file in memory)
- Limited concurrency (max 4 uploads)
- Connection pooling

### CPU
- Event-driven file watching (no polling)
- Async I/O (non-blocking)
- Semaphore-based concurrency control

### Network
- Parallel uploads via presigned URLs (4 concurrent)
- Direct S3 upload (no backend bottleneck)
- Connection reuse
- Retry with exponential backoff

## Monitoring

Logs are written to:
- Console (colored output)
- File: `ftp_processor.log` (with rotation)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=.

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html
```

## Troubleshooting

> 📖 **See [SETUP_GUIDE.md](SETUP_GUIDE.md#-troubleshooting) for detailed troubleshooting**

### Quick Checks

**Files not being processed?**
```bash
# Check if watcher is running
tail -f ftp_processor.log | grep "File watcher started"

# Verify directory structure
tree /var/ftp/uploads -L 4

# Check permissions (processor needs READ access)
ls -la /var/ftp/uploads/username_userid/ftp/camera1/
```

**API errors?**
```bash
# Test API token
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://prod.fotosfolio.com/storage/validate/123/1000

# Check logs for specific errors
grep ERROR ftp_processor.log
```

**Upload failures?**
```bash
# Check if presigned URLs are valid
grep "presigned URL" ftp_processor.log

# View failed uploads
grep "Upload failed" ftp_processor.log -A 3
```

### Common Issues

| Problem | Solution |
|---------|----------|
| "FTP_ROOT_DIR does not exist" | Update `FTP_ROOT_DIR` in `.env` to point to your actual FTP directory |
| "No valid files in batch" | Check directory structure matches: `username_userid/ftp/cameraX/` |
| "Storage validation failed" | Verify `API_AUTH_TOKEN` is correct in `.env` |
| "Upload failed after retries" | Check network connectivity to S3, increase `MAX_RETRIES` |
| Files not detected | Wait for file upload to complete (file must be closed) |

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
# ftpWatcher
