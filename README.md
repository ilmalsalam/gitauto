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
check_interval: 60  # Check every 1 minute
repositories:
  - path: "/path/to/your/repo"
    branch: "main"
```

3. Set up the service:
   Ada dua cara untuk menjalankan service ini:

### 1. Sebagai Daemon Process (Direkomendasikan)

```bash
# Jalankan script sebagai daemon
python3 git_auto_pull.py --daemon
```

Script akan berjalan di background dan log akan disimpan di `git_auto.log` dalam direktori yang sama.

Untuk menghentikan service:

```bash
# Cari PID dari process
ps aux | grep git_auto_pull.py

# Matikan process
kill <PID>  # ganti <PID> dengan nomor yang didapat
```

### 2. Sebagai Service Systemd (Opsional)

1. Edit the service file to set your username

```bash
sudo nano git-auto-pull.service
```

2. Setup the systemd service:

```bash
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

File `config.yml`:

- `check_interval`: Interval pengecekan dalam detik
- `repositories`: Daftar repository yang akan dimonitor
  - `path`: Path absolut ke repository
  - `branch`: Nama branch yang akan dimonitor
  - `type`: (Opsional) Tipe repository - tulis "nextjs" untuk repository NextJS
  - `pm2_ids`: List ID proses PM2 yang perlu di-restart [1, 2, dst]
  - `build_command`: (Khusus NextJS) Perintah build yang akan dijalankan

Contoh konfigurasi lengkap:

```yaml
check_interval: 60  # Check setiap 1 menit
repositories:
  # Repository NextJS
  - path: "/home/username/nextjs-app"
    branch: "master"
    type: "nextjs"
    pm2_ids: [1, 2]
    build_command: "npm run build"
  
  # Repository Standard
  - path: "/home/username/standard-app"
    branch: "main"
    pm2_ids: [3]
```

## Fitur PM2

Script akan menangani proses PM2 untuk semua tipe repository:

1. Untuk repository standard:

   - Menghentikan proses PM2 yang ditentukan
   - Melakukan git pull
   - Menjalankan kembali proses PM2
2. Untuk repository NextJS:

   - Menghentikan proses PM2 yang ditentukan
   - Melakukan git pull
   - Menjalankan perintah build
   - Menjalankan kembali proses PM2

Jika terjadi error:

- Error akan dicatat di log
- Proses PM2 akan otomatis dicoba untuk dijalankan kembali
- Detail error dapat diperiksa di file log

## Troubleshooting

1. Make sure the user running the service has proper Git credentials and permissions
2. Check the logs for any errors
3. Ensure the repository paths in config.yml are correct
4. Verify the branches specified exist in the remote repository
