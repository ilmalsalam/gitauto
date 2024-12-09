# Git Auto Pull Service

This service automatically pulls changes from specified Git repositories when updates are detected on configured branches.

## Setup Instructions

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your repositories:
Edit `config.yml` and add your repository paths and branches:
```yaml
check_interval: 300  # Check every 5 minutes
repositories:
  - path: "/path/to/your/repo"
    branch: "main"
```

3. Set up the systemd service:
```bash
# Edit the service file to set your username
sudo nano git-auto-pull.service

# Copy the service file to systemd directory
sudo cp git-auto-pull.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Start the service
sudo systemctl start git-auto-pull

# Enable the service to start on boot
sudo systemctl enable git-auto-pull
```

4. Check service status:
```bash
sudo systemctl status git-auto-pull
```

5. View logs:
```bash
# View service logs
sudo journalctl -u git-auto-pull

# View application logs
tail -f git_auto_pull.log
```

## Configuration

- `check_interval`: Time in seconds between checking for updates
- `repositories`: List of repositories to monitor
  - `path`: Absolute path to the repository
  - `branch`: Branch name to monitor

## Troubleshooting

1. Make sure the user running the service has proper Git credentials and permissions
2. Check the logs for any errors
3. Ensure the repository paths in config.yml are correct
4. Verify the branches specified exist in the remote repository
