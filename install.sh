#!/bin/bash

#############################################################################
# FTP File Processor - Automated Installation Script
# This script handles complete installation and configuration
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/ftp-processor"
SERVICE_USER="ftpprocessor"
VENV_DIR="$INSTALL_DIR/venv"
LOG_DIR="/var/log/ftp-processor"
SYSTEMD_SERVICE="/etc/systemd/system/ftp-processor.service"

#############################################################################
# Helper Functions
#############################################################################

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        echo "Please run: sudo $0"
        exit 1
    fi
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.11 or higher first"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        print_error "Python 3.11 or higher required (found $PYTHON_VERSION)"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION detected"
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    if [ -n "$default" ]; then
        read -p "$(echo -e ${YELLOW}$prompt ${NC}[${GREEN}$default${NC}]: )" input
        eval "$var_name=${input:-$default}"
    else
        while [ -z "${!var_name}" ]; do
            read -p "$(echo -e ${YELLOW}$prompt ${NC}[${RED}required${NC}]: )" input
            eval "$var_name=$input"
            if [ -z "${!var_name}" ]; then
                print_error "This field is required!"
            fi
        done
    fi
}

prompt_password() {
    local prompt="$1"
    local var_name="$2"

    while [ -z "${!var_name}" ]; do
        read -sp "$(echo -e ${YELLOW}$prompt ${NC}[${RED}required${NC}]: )" input
        echo
        eval "$var_name=$input"
        if [ -z "${!var_name}" ]; then
            print_error "This field is required!"
        fi
    done
}

#############################################################################
# Installation Steps
#############################################################################

step_welcome() {
    clear
    print_header "FTP File Processor - Automated Installer"
    echo
    echo "This script will:"
    echo "  1. Create dedicated user and directories"
    echo "  2. Install application files"
    echo "  3. Create Python virtual environment"
    echo "  4. Install dependencies"
    echo "  5. Configure the application"
    echo "  6. Set up systemd service"
    echo "  7. Start the service"
    echo
    print_warning "Installation directory: $INSTALL_DIR"
    print_warning "Service user: $SERVICE_USER"
    print_warning "Log directory: $LOG_DIR"
    echo
    read -p "Press Enter to continue or Ctrl+C to cancel..."
}

step_check_requirements() {
    print_header "Step 1: Checking Requirements"

    check_root
    check_python

    # Check for required commands
    for cmd in systemctl curl; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed"
            exit 1
        fi
        print_success "$cmd is available"
    done
}

step_create_user() {
    print_header "Step 2: Creating System User"

    if id "$SERVICE_USER" &>/dev/null; then
        print_warning "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/false -d "$INSTALL_DIR" -m "$SERVICE_USER"
        print_success "User $SERVICE_USER created"
    fi
}

step_create_directories() {
    print_header "Step 3: Creating Directories"

    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    print_success "Created $INSTALL_DIR"

    # Create log directory
    mkdir -p "$LOG_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    print_success "Created $LOG_DIR"
}

step_copy_files() {
    print_header "Step 4: Installing Application Files"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Copy Python files
    for file in main.py config.py logger.py watcher.py processor.py api_client.py storage_client.py utils.py; do
        if [ -f "$SCRIPT_DIR/$file" ]; then
            cp "$SCRIPT_DIR/$file" "$INSTALL_DIR/"
            print_success "Copied $file"
        else
            print_error "Missing file: $file"
            exit 1
        fi
    done

    # Copy requirements.txt
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
        print_success "Copied requirements.txt"
    else
        print_error "Missing requirements.txt"
        exit 1
    fi
}

step_create_virtualenv() {
    print_header "Step 5: Creating Virtual Environment"

    cd "$INSTALL_DIR"

    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"

    source "$VENV_DIR/bin/activate"

    print_info "Installing Python dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1

    print_success "Dependencies installed"

    deactivate
}

step_configure() {
    print_header "Step 6: Configuration"

    echo
    echo "Please provide the following configuration:"
    echo

    # API Configuration
    print_info "API Configuration"
    prompt_input "Backend API URL" "https://prod.fotosfolio.com" API_BASE_URL
    prompt_password "API Bearer Token" API_AUTH_TOKEN
    prompt_input "API Timeout (seconds)" "30" API_TIMEOUT
    echo

    # FTP Configuration
    print_info "FTP Configuration"
    prompt_input "FTP Root Directory" "/var/ftp/uploads" FTP_ROOT_DIR

    # Validate FTP directory exists
    if [ ! -d "$FTP_ROOT_DIR" ]; then
        print_warning "FTP directory does not exist: $FTP_ROOT_DIR"
        read -p "Create it now? (y/n): " create_ftp
        if [ "$create_ftp" = "y" ] || [ "$create_ftp" = "Y" ]; then
            mkdir -p "$FTP_ROOT_DIR"
            chmod 755 "$FTP_ROOT_DIR"
            print_success "Created FTP directory"
        else
            print_error "FTP directory must exist before continuing"
            exit 1
        fi
    fi
    echo

    # Processing Configuration
    print_info "Processing Configuration (press Enter for defaults)"
    prompt_input "Batch Size (files per batch)" "10" BATCH_SIZE
    prompt_input "Max Concurrent Uploads" "4" MAX_CONCURRENT_UPLOADS
    prompt_input "Batch Timeout (seconds)" "30" BATCH_TIMEOUT_SECONDS
    echo

    # Optional S3 Bucket Name
    print_info "Optional: S3 Bucket Name (may be needed for API)"
    prompt_input "S3 Bucket Name" "" S3_BUCKET_NAME
    echo

    # Create .env file
    cat > "$INSTALL_DIR/.env" << EOF
# API Configuration
API_BASE_URL=$API_BASE_URL
API_AUTH_TOKEN=$API_AUTH_TOKEN
API_TIMEOUT=$API_TIMEOUT

# S3 Configuration
S3_BUCKET_NAME=$S3_BUCKET_NAME

# FTP Configuration
FTP_ROOT_DIR=$FTP_ROOT_DIR

# Processing Configuration
BATCH_SIZE=$BATCH_SIZE
MAX_CONCURRENT_UPLOADS=$MAX_CONCURRENT_UPLOADS
BATCH_TIMEOUT_SECONDS=$BATCH_TIMEOUT_SECONDS

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_MULTIPLIER=2
RETRY_INITIAL_DELAY=1

# Upload Configuration
UPLOAD_CHUNK_SIZE=1048576

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/ftp_processor.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
EOF

    chmod 600 "$INSTALL_DIR/.env"
    print_success "Configuration saved to $INSTALL_DIR/.env"
}

step_set_permissions() {
    print_header "Step 7: Setting Permissions"

    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    print_success "Set ownership of $INSTALL_DIR"

    # Give read access to FTP directory
    if [ -d "$FTP_ROOT_DIR" ]; then
        # Add service user to FTP group if it exists
        FTP_GROUP=$(stat -c '%G' "$FTP_ROOT_DIR")
        usermod -a -G "$FTP_GROUP" "$SERVICE_USER" 2>/dev/null || true
        print_success "Added $SERVICE_USER to $FTP_GROUP group"
    fi
}

step_create_service() {
    print_header "Step 8: Creating Systemd Service"

    cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=FTP File Processor
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR

# Logging
StandardOutput=append:$LOG_DIR/stdout.log
StandardError=append:$LOG_DIR/stderr.log

[Install]
WantedBy=multi-user.target
EOF

    print_success "Systemd service created"

    systemctl daemon-reload
    print_success "Systemd daemon reloaded"
}

step_test_configuration() {
    print_header "Step 9: Testing Configuration"

    cd "$INSTALL_DIR"
    source "$VENV_DIR/bin/activate"

    print_info "Validating configuration..."
    if python -c "from config import Config; Config.validate(); print('Configuration is valid!')" 2>&1; then
        print_success "Configuration is valid"
    else
        print_error "Configuration validation failed"
        print_warning "Please check your settings in $INSTALL_DIR/.env"
        deactivate
        exit 1
    fi

    deactivate
}

step_enable_service() {
    print_header "Step 10: Enabling Service"

    systemctl enable ftp-processor
    print_success "Service enabled (will start on boot)"

    systemctl start ftp-processor
    print_success "Service started"

    sleep 2

    if systemctl is-active --quiet ftp-processor; then
        print_success "Service is running!"
    else
        print_error "Service failed to start"
        print_info "Check logs with: journalctl -u ftp-processor -n 50"
        exit 1
    fi
}

step_complete() {
    print_header "Installation Complete!"

    echo
    print_success "FTP File Processor has been installed and started"
    echo
    echo "Service Status:"
    systemctl status ftp-processor --no-pager | head -n 10
    echo
    echo "Useful Commands:"
    echo "  View logs:        tail -f $LOG_DIR/ftp_processor.log"
    echo "  Service status:   systemctl status ftp-processor"
    echo "  Restart service:  systemctl restart ftp-processor"
    echo "  Stop service:     systemctl stop ftp-processor"
    echo "  View live logs:   journalctl -u ftp-processor -f"
    echo "  Edit config:      nano $INSTALL_DIR/.env"
    echo
    echo "Configuration:"
    echo "  Install dir:      $INSTALL_DIR"
    echo "  Config file:      $INSTALL_DIR/.env"
    echo "  Log directory:    $LOG_DIR"
    echo "  FTP directory:    $FTP_ROOT_DIR"
    echo
    print_warning "After editing .env, restart service: systemctl restart ftp-processor"
    echo
}

#############################################################################
# Uninstall Function
#############################################################################

uninstall() {
    print_header "Uninstalling FTP File Processor"

    echo
    print_warning "This will:"
    echo "  - Stop and disable the service"
    echo "  - Remove system user $SERVICE_USER"
    echo "  - Delete $INSTALL_DIR"
    echo "  - Delete $LOG_DIR"
    echo "  - Remove systemd service"
    echo
    read -p "Are you sure? (type 'yes' to confirm): " confirm

    if [ "$confirm" != "yes" ]; then
        print_info "Uninstall cancelled"
        exit 0
    fi

    # Stop service
    if systemctl is-active --quiet ftp-processor; then
        systemctl stop ftp-processor
        print_success "Service stopped"
    fi

    # Disable service
    if systemctl is-enabled --quiet ftp-processor 2>/dev/null; then
        systemctl disable ftp-processor
        print_success "Service disabled"
    fi

    # Remove systemd service
    if [ -f "$SYSTEMD_SERVICE" ]; then
        rm "$SYSTEMD_SERVICE"
        systemctl daemon-reload
        print_success "Systemd service removed"
    fi

    # Remove directories
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        print_success "Removed $INSTALL_DIR"
    fi

    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        print_success "Removed $LOG_DIR"
    fi

    # Remove user
    if id "$SERVICE_USER" &>/dev/null; then
        userdel "$SERVICE_USER" 2>/dev/null || true
        print_success "Removed user $SERVICE_USER"
    fi

    print_success "Uninstall complete!"
}

#############################################################################
# Main Installation Flow
#############################################################################

main() {
    case "${1:-}" in
        --uninstall)
            check_root
            uninstall
            ;;
        --help)
            echo "FTP File Processor - Installation Script"
            echo
            echo "Usage:"
            echo "  sudo ./install.sh              Install the application"
            echo "  sudo ./install.sh --uninstall  Uninstall the application"
            echo "  ./install.sh --help            Show this help"
            ;;
        *)
            step_welcome
            step_check_requirements
            step_create_user
            step_create_directories
            step_copy_files
            step_create_virtualenv
            step_configure
            step_set_permissions
            step_create_service
            step_test_configuration
            step_enable_service
            step_complete
            ;;
    esac
}

# Run main function
main "$@"
