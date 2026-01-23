#!/bin/bash

# FTP Server Setup Script
# Sets up vsftpd with chroot jail and proper directory structure

set -e

echo "========================================="
echo "FTP Server Setup"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install vsftpd
echo "Installing vsftpd..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y vsftpd
elif command -v yum &> /dev/null; then
    yum install -y vsftpd
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm vsftpd
else
    echo "Unsupported package manager. Please install vsftpd manually."
    exit 1
fi

# Create FTP root directory
FTP_ROOT="/ftp_root"
echo "Creating FTP root directory: $FTP_ROOT"
mkdir -p "$FTP_ROOT"
chmod 755 "$FTP_ROOT"

# Backup original vsftpd config
if [ -f /etc/vsftpd.conf ]; then
    echo "Backing up original vsftpd.conf..."
    cp /etc/vsftpd.conf /etc/vsftpd.conf.backup.$(date +%Y%m%d_%H%M%S)
fi

# Copy new vsftpd config
echo "Installing vsftpd configuration..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/vsftpd.conf" /etc/vsftpd.conf

# Create vsftpd secure chroot directory
mkdir -p /var/run/vsftpd/empty

# Function to create FTP user
create_ftp_user() {
    local username=$1
    local userid=$2
    local password=$3
    
    local username_userid="${username}_${userid}"
    local user_home="$FTP_ROOT/$username_userid"
    
    echo "Creating FTP user: $username_userid"
    
    # Create system user (no shell access)
    if id "$username_userid" &>/dev/null; then
        echo "User $username_userid already exists, skipping..."
    else
        useradd -d "$user_home" -s /usr/sbin/nologin "$username_userid"
        echo "$username_userid:$password" | chpasswd
    fi
    
    # Create directory structure
    mkdir -p "$user_home/ftp"
    
    # Set ownership and permissions
    chown root:root "$user_home"
    chmod 755 "$user_home"
    
    chown "$username_userid:$username_userid" "$user_home/ftp"
    chmod 755 "$user_home/ftp"
    
    echo "User $username_userid created successfully"
    echo "  Home: $user_home"
    echo "  Upload directory: $user_home/ftp/"
}

# Example: Create test users
# Uncomment and modify as needed
# create_ftp_user "testuser" "123" "testpassword"
# create_ftp_user "camera1" "456" "camera1pass"

echo ""
echo "========================================="
echo "Manual User Creation"
echo "========================================="
echo "To create FTP users, run:"
echo "  sudo ./setup_ftp.sh create_user <username> <userid> <password>"
echo ""
echo "Example:"
echo "  sudo ./setup_ftp.sh create_user john 123 mypassword"
echo ""
echo "This will create:"
echo "  - System user: john_123"
echo "  - Home directory: /ftp_root/john_123/"
echo "  - Upload directory: /ftp_root/john_123/ftp/"
echo "========================================="

# Handle command line arguments for user creation
if [ "$1" = "create_user" ]; then
    if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
        echo "Usage: $0 create_user <username> <userid> <password>"
        exit 1
    fi
    create_ftp_user "$2" "$3" "$4"
    exit 0
fi

# Enable and start vsftpd
echo "Enabling and starting vsftpd..."
systemctl enable vsftpd
systemctl restart vsftpd

# Check status
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
systemctl status vsftpd --no-pager
echo ""
echo "FTP server is running on port 21"
echo "Passive ports: 40000-40100"
echo ""
echo "Next steps:"
echo "1. Create FTP users using the command above"
echo "2. Configure firewall to allow ports 21 and 40000-40100"
echo "3. Test FTP connection"
echo ""
