import os
import time
import subprocess
import logging
from datetime import datetime
import yaml
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('git_auto_pull.log'),
        logging.StreamHandler()
    ]
)

def load_config():
    with open('config.yml', 'r') as file:
        return yaml.safe_load(file)

def handle_pm2_processes(pm2_ids, action="restart"):
    """Handle PM2 processes with specified action (stop/start/restart)"""
    try:
        for pm2_id in pm2_ids:
            logging.info(f"{action.capitalize()}ing PM2 process {pm2_id}")
            subprocess.run(['pm2', action, str(pm2_id)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during PM2 {action}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during PM2 {action}: {str(e)}")
        return False

def handle_nextjs_build(repo_path, pm2_ids, build_command):
    try:
        # Stop PM2 processes
        handle_pm2_processes(pm2_ids, "stop")

        # Run build command
        logging.info(f"Running build command: {build_command}")
        os.chdir(repo_path)
        process = subprocess.Popen(
            build_command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Capture and log output in real-time
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            
            if output:
                logging.info(f"Build output: {output.strip()}")
            if error:
                logging.error(f"Build error: {error.strip()}")
            
            # Check if process has finished
            if output == '' and error == '' and process.poll() is not None:
                break
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, build_command)

        # Start PM2 processes
        handle_pm2_processes(pm2_ids, "start")

        logging.info("NextJS build process completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during build process: {str(e)}")
        # Try to restart PM2 processes in case of failure
        handle_pm2_processes(pm2_ids, "start")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during build: {str(e)}")
        return False

def handle_repository_update(repo_path, branch, repo_type, pm2_ids=None, build_command=None):
    """Handle repository update including PM2 management"""
    try:
        # Change to repository directory
        os.chdir(repo_path)
        
        # Fetch the latest changes
        subprocess.run(['git', 'fetch', 'origin', branch], check=True)
        
        # Get the current and remote HEADs
        current = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        remote = subprocess.check_output(['git', 'rev-parse', f'origin/{branch}']).decode().strip()
        
        # If there are changes, handle the update
        if current != remote:
            logging.info(f"Changes detected in {repo_path} on branch {branch}")
            
            # Stop PM2 processes if specified
            if pm2_ids:
                handle_pm2_processes(pm2_ids, "stop")
            
            # Pull changes
            subprocess.run(['git', 'checkout', branch], check=True)
            subprocess.run(['git', 'pull', 'origin', branch], check=True)
            logging.info(f"Successfully pulled changes for {repo_path} on branch {branch}")
            
            # Handle NextJS build if necessary
            if repo_type == 'nextjs' and build_command:
                logging.info("Running NextJS build process")
                os.chdir(repo_path)
                subprocess.run(build_command.split(), check=True)
            
            # Start PM2 processes if specified
            if pm2_ids:
                handle_pm2_processes(pm2_ids, "start")
            
            return True
        return False
    except Exception as e:
        logging.error(f"Error handling repository update: {str(e)}")
        # Try to restart PM2 processes in case of failure
        if pm2_ids:
            handle_pm2_processes(pm2_ids, "start")
        return False

def daemonize():
    # Get the absolute path of the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, 'git_auto.log')

    # First fork (detaches from parent)
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            sys.exit(0)
    except OSError as err:
        sys.stderr.write(f'fork #1 failed: {err}\n')
        sys.exit(1)

    # Decouple from parent environment
    os.chdir(script_dir)  # Change to script directory instead of root
    os.umask(0)
    os.setsid()

    # Second fork (relinquish session leadership)
    try:
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            sys.exit(0)
    except OSError as err:
        sys.stderr.write(f'fork #2 failed: {err}\n')
        sys.exit(1)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(log_file, 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())

def main():
    config = load_config()
    check_interval = config.get('check_interval', 300)  # Default 5 minutes
    
    while True:
        for repo in config['repositories']:
            repo_path = repo['path']
            branch = repo['branch']
            repo_type = repo.get('type', 'standard')
            pm2_ids = repo.get('pm2_ids', [])
            build_command = repo.get('build_command')
            
            logging.info(f"Checking repository: {repo_path} on branch {branch}")
            handle_repository_update(repo_path, branch, repo_type, pm2_ids, build_command)
        
        time.sleep(check_interval)

if __name__ == "__main__":
    logging.info("Starting Git Auto Pull Service")
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        daemonize()
    main()
