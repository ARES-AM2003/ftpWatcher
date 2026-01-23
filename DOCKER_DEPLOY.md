# Docker Deployment Guide - FTP File Processor

> **Simple, one-command deployment using Docker**

---

## 🚀 Quick Start (3 Steps)

### Step 1: Create `.env` file

```bash
cat > .env << 'EOF'
# API Configuration (REQUIRED)
API_BASE_URL=https://prod.fotosfolio.com
API_AUTH_TOKEN=your_actual_bearer_token_here
API_TIMEOUT=30

# S3 Configuration (Optional)
S3_BUCKET_NAME=your-bucket-name

# FTP Configuration (REQUIRED)
FTP_ROOT_DIR=/ftp_root

# Processing Configuration
BATCH_SIZE=10
MAX_CONCURRENT_UPLOADS=4
BATCH_TIMEOUT_SECONDS=30

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_MULTIPLIER=2
RETRY_INITIAL_DELAY=1

# Upload Configuration
UPLOAD_CHUNK_SIZE=1048576

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/app/logs/ftp_processor.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
EOF
```

**Edit the file and set your values:**
```bash
nano .env
```

### Step 2: Build Docker Image

```bash
# Build the image
docker build -t ftp-processor:latest .
```

### Step 3: Run Container

```bash
# Run with your FTP directory mounted
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -v /path/to/your/ftp:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest
```

**Replace `/path/to/your/ftp`** with your actual FTP directory!

---

## 📋 Complete Examples

### Example 1: Basic Deployment

```bash
# Your FTP directory is at: /var/ftp/uploads

# 1. Create .env (edit with your values)
cp .env.example .env
nano .env

# 2. Build image
docker build -t ftp-processor:latest .

# 3. Run container
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest

# 4. Check logs
docker logs -f ftp-file-processor
```

### Example 2: Using Docker Compose

```bash
# 1. Edit docker-compose.yml
nano docker-compose.yml

# Change this line to your FTP path:
#   - /path/to/your/ftp:/ftp_root:ro
# To:
#   - /var/ftp/uploads:/ftp_root:ro

# 2. Create .env file
cp .env.example .env
nano .env

# 3. Start
docker-compose up -d

# 4. View logs
docker-compose logs -f ftp-processor
```

### Example 3: With Specific Timezone

```bash
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -e TZ=America/New_York \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest
```

---

## 🔧 Configuration

### Required Environment Variables

Create `.env` file with these **required** values:

```bash
# REQUIRED
API_BASE_URL=https://prod.fotosfolio.com
API_AUTH_TOKEN=your_actual_token

# REQUIRED - Leave as /ftp_root (mapped via -v flag)
FTP_ROOT_DIR=/ftp_root
```

### Optional Environment Variables

```bash
# Processing
BATCH_SIZE=10                    # Files per batch
MAX_CONCURRENT_UPLOADS=4         # Parallel uploads
BATCH_TIMEOUT_SECONDS=30         # Wait time for batch

# Retry
MAX_RETRIES=3                    # Retry attempts
RETRY_INITIAL_DELAY=1            # Initial delay (seconds)
RETRY_BACKOFF_MULTIPLIER=2       # Exponential backoff

# Upload
UPLOAD_CHUNK_SIZE=1048576        # 1MB chunks

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
```

### Volume Mounts Explained

```bash
-v /var/ftp/uploads:/ftp_root:ro
#  └─── Host Path ──┘ └Container┘ └ReadOnly
#                       Path

-v $(pwd)/logs:/app/logs
#  └─ Host Path ─┘ └Container Path┘
```

---

## 📦 Pre-built Image (Optional)

If you publish to Docker Hub:

```bash
# Pull pre-built image
docker pull your-dockerhub/ftp-processor:latest

# Run directly (no build needed!)
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  your-dockerhub/ftp-processor:latest
```

### To publish your image:

```bash
# Login to Docker Hub
docker login

# Tag image
docker tag ftp-processor:latest your-dockerhub/ftp-processor:latest

# Push
docker push your-dockerhub/ftp-processor:latest
```

---

## 🎮 Container Management

### View Logs

```bash
# Real-time logs
docker logs -f ftp-file-processor

# Last 100 lines
docker logs --tail 100 ftp-file-processor

# With timestamps
docker logs -f --timestamps ftp-file-processor

# Logs from last 1 hour
docker logs --since 1h ftp-file-processor
```

### Check Status

```bash
# Is container running?
docker ps | grep ftp-file-processor

# Container details
docker inspect ftp-file-processor

# Resource usage
docker stats ftp-file-processor
```

### Restart/Stop/Start

```bash
# Restart
docker restart ftp-file-processor

# Stop
docker stop ftp-file-processor

# Start
docker start ftp-file-processor

# Remove (stop first!)
docker stop ftp-file-processor
docker rm ftp-file-processor
```

### Update Configuration

```bash
# 1. Edit .env
nano .env

# 2. Restart container
docker restart ftp-file-processor

# Or recreate:
docker stop ftp-file-processor
docker rm ftp-file-processor
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest
```

### Execute Commands Inside Container

```bash
# Open shell
docker exec -it ftp-file-processor bash

# Check Python version
docker exec ftp-file-processor python --version

# Test configuration
docker exec ftp-file-processor python -c "from config import Config; print(Config.display())"

# View file structure
docker exec ftp-file-processor ls -la /ftp_root
```

---

## 🧪 Testing Deployment

### Test 1: Verify Container is Running

```bash
docker ps | grep ftp-file-processor
```

**Expected output:**
```
CONTAINER ID   IMAGE                    STATUS          PORTS     NAMES
abc123def456   ftp-processor:latest     Up 2 minutes              ftp-file-processor
```

### Test 2: Check Logs

```bash
docker logs ftp-file-processor | head -20
```

**Expected output:**
```
================================================================================
FTP Upload Processor Starting
================================================================================

Configuration:
  API Base URL: https://prod.fotosfolio.com
  API Auth Token: ********************
  ...
  FTP Root Dir: /ftp_root

Application started successfully
Monitoring FTP directories for new uploads...
File watcher started, monitoring: /ftp_root
```

### Test 3: Verify FTP Mount

```bash
docker exec ftp-file-processor ls -la /ftp_root
```

**Expected output:** Your FTP directory structure

### Test 4: Upload a Test File

```bash
# Copy test file to FTP directory
cp ~/test.jpg /var/ftp/uploads/john_123/ftp/camera1/

# Watch logs
docker logs -f ftp-file-processor
```

**Expected:** File detection and upload logs

---

## 🔍 Troubleshooting

### Problem: Container exits immediately

**Check logs:**
```bash
docker logs ftp-file-processor
```

**Common causes:**
- Missing `API_AUTH_TOKEN` in `.env`
- Invalid `FTP_ROOT_DIR`
- Configuration validation failed

**Solution:**
```bash
# Validate .env file
cat .env | grep API_AUTH_TOKEN
cat .env | grep FTP_ROOT_DIR

# Check what's failing
docker logs ftp-file-processor 2>&1 | grep -i error
```

### Problem: "FTP_ROOT_DIR does not exist"

**Cause:** Volume not mounted correctly

**Solution:**
```bash
# Check if mount exists inside container
docker exec ftp-file-processor ls -la /ftp_root

# Verify volume mount
docker inspect ftp-file-processor | grep -A 5 Mounts

# Recreate with correct mount
docker stop ftp-file-processor
docker rm ftp-file-processor
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest
```

### Problem: Files not being detected

**Check:**
```bash
# 1. Verify watcher is running
docker logs ftp-file-processor | grep "File watcher started"

# 2. Check FTP directory structure inside container
docker exec ftp-file-processor tree /ftp_root -L 4

# 3. Verify permissions
docker exec ftp-file-processor ls -la /ftp_root/username_123/ftp/camera1/

# 4. Enable debug logging
# Edit .env: LOG_LEVEL=DEBUG
# Restart: docker restart ftp-file-processor
```

### Problem: Permission denied on FTP files

**Solution:**
```bash
# Check file permissions on host
ls -la /var/ftp/uploads/username_123/ftp/camera1/

# Make readable by all (if safe)
chmod -R o+r /var/ftp/uploads/

# Or add container user to FTP group (advanced)
# Get container user UID
docker exec ftp-file-processor id
# Adjust host permissions accordingly
```

### Problem: Cannot connect to API

**Check:**
```bash
# Test from inside container
docker exec ftp-file-processor curl -I https://prod.fotosfolio.com

# Check API token
docker exec ftp-file-processor printenv API_AUTH_TOKEN

# Test API call
docker exec ftp-file-processor python -c "
from api_client import APIClient
import asyncio

async def test():
    async with APIClient() as client:
        print('API client created successfully')
        
asyncio.run(test())
"
```

---

## 🎯 Best Practices

### 1. Security

```bash
# ✅ Use read-only mount for FTP directory
-v /var/ftp/uploads:/ftp_root:ro

# ✅ Protect .env file
chmod 600 .env

# ✅ Don't expose ports (not needed)
# No -p flag required

# ✅ Use secrets for sensitive data (Docker Swarm/Kubernetes)
docker secret create api_token api_token.txt
```

### 2. Resource Limits

```bash
# Limit memory and CPU
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --memory="512m" \
  --memory-swap="1g" \
  --cpus="1.0" \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest
```

### 3. Logging

```bash
# Limit Docker logs (prevent disk fill)
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest
```

### 4. Health Checks

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' ftp-file-processor

# View health check logs
docker inspect --format='{{json .State.Health}}' ftp-file-processor | jq
```

### 5. Backup Configuration

```bash
# Backup .env and logs
tar -czf ftp-processor-backup-$(date +%Y%m%d).tar.gz .env logs/

# Restore
tar -xzf ftp-processor-backup-YYYYMMDD.tar.gz
```

---

## 🔄 Update/Upgrade

### Update Application Code

```bash
# 1. Pull latest code
git pull

# 2. Rebuild image
docker build -t ftp-processor:latest .

# 3. Stop old container
docker stop ftp-file-processor
docker rm ftp-file-processor

# 4. Run new version
docker run -d \
  --name ftp-file-processor \
  --restart unless-stopped \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:latest

# 5. Verify
docker logs -f ftp-file-processor
```

### Zero-Downtime Update (Using Two Containers)

```bash
# 1. Build new image with version tag
docker build -t ftp-processor:v2 .

# 2. Start new container (different name)
docker run -d \
  --name ftp-file-processor-v2 \
  --restart unless-stopped \
  --env-file .env \
  -v /var/ftp/uploads:/ftp_root:ro \
  -v $(pwd)/logs:/app/logs \
  ftp-processor:v2

# 3. Verify new container works
docker logs ftp-file-processor-v2

# 4. Stop old container
docker stop ftp-file-processor
docker rm ftp-file-processor

# 5. Rename new container
docker rename ftp-file-processor-v2 ftp-file-processor
```

---

## 📊 Monitoring

### Container Stats

```bash
# Real-time stats
docker stats ftp-file-processor

# Get specific metric
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" ftp-file-processor
```

### Application Logs

```bash
# Application log file
tail -f logs/ftp_processor.log

# Count processed files today
grep "Upload completed:" logs/ftp_processor.log | grep "$(date +%Y-%m-%d)" | wc -l

# Check for errors
grep ERROR logs/ftp_processor.log | tail -20
```

### Export Logs

```bash
# Export Docker logs
docker logs ftp-file-processor > docker-logs-$(date +%Y%m%d).log

# Export application logs
cp logs/ftp_processor.log backups/ftp_processor-$(date +%Y%m%d).log
```

---

## 🗑️ Cleanup

### Remove Container Only

```bash
docker stop ftp-file-processor
docker rm ftp-file-processor
```

### Remove Container and Image

```bash
docker stop ftp-file-processor
docker rm ftp-file-processor
docker rmi ftp-processor:latest
```

### Full Cleanup (Including Logs)

```bash
# Stop and remove container
docker stop ftp-file-processor
docker rm ftp-file-processor

# Remove image
docker rmi ftp-processor:latest

# Remove logs (CAREFUL!)
rm -rf logs/

# Remove .env (CAREFUL!)
rm .env
```

### Cleanup Docker System

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Clean everything unused
docker system prune -a --volumes
```

---

## 🚀 Production Deployment Checklist

- [ ] `.env` file created with real credentials
- [ ] `API_AUTH_TOKEN` is valid and working
- [ ] FTP directory path is correct
- [ ] FTP directory structure follows: `username_userid/ftp/camera1/`
- [ ] Container has read access to FTP directory
- [ ] Logs directory exists and is writable
- [ ] Tested with a sample file upload
- [ ] Monitoring/alerting set up
- [ ] Log rotation configured
- [ ] Backup strategy in place
- [ ] Resource limits set (if needed)
- [ ] Auto-restart enabled (`--restart unless-stopped`)

---

## 💡 Quick Commands Reference

```bash
# Build
docker build -t ftp-processor:latest .

# Run
docker run -d --name ftp-file-processor --restart unless-stopped --env-file .env -v /var/ftp/uploads:/ftp_root:ro -v $(pwd)/logs:/app/logs ftp-processor:latest

# Logs
docker logs -f ftp-file-processor

# Restart
docker restart ftp-file-processor

# Stop
docker stop ftp-file-processor

# Remove
docker rm ftp-file-processor

# Shell
docker exec -it ftp-file-processor bash

# Stats
docker stats ftp-file-processor
```

---

**Need help?** Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting!