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

def git_pull(repo_path, branch):
    try:
        # Change to repository directory
        os.chdir(repo_path)
        
        # Fetch the latest changes
        subprocess.run(['git', 'fetch', 'origin', branch], check=True)
        
        # Get the current and remote HEADs
        current = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        remote = subprocess.check_output(['git', 'rev-parse', f'origin/{branch}']).decode().strip()
        
        # If there are changes, pull them
        if current != remote:
            logging.info(f"Changes detected in {repo_path} on branch {branch}")
            subprocess.run(['git', 'checkout', branch], check=True)
            subprocess.run(['git', 'pull', 'origin', branch], check=True)
            logging.info(f"Successfully pulled changes for {repo_path} on branch {branch}")
            return True
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during git operations: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return False

def handle_nextjs_build(repo_path, pm2_ids, build_command):
    try:
        # Stop PM2 processes
        for pm2_id in pm2_ids:
            logging.info(f"Stopping PM2 process {pm2_id}")
            subprocess.run(['pm2', 'stop', str(pm2_id)], check=True)

        # Run build command
        logging.info(f"Running build command: {build_command}")
        os.chdir(repo_path)
        subprocess.run(build_command.split(), check=True)

        # Start PM2 processes
        for pm2_id in pm2_ids:
            logging.info(f"Starting PM2 process {pm2_id}")
            subprocess.run(['pm2', 'start', str(pm2_id)], check=True)

        logging.info("NextJS build process completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during build process: {str(e)}")
        # Try to restart PM2 processes in case of failure
        for pm2_id in pm2_ids:
            try:
                subprocess.run(['pm2', 'start', str(pm2_id)], check=True)
            except:
                logging.error(f"Failed to restart PM2 process {pm2_id}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during build: {str(e)}")
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
            
            logging.info(f"Checking repository: {repo_path} on branch {branch}")
            changes_pulled = git_pull(repo_path, branch)
            
            # Handle NextJS build if necessary
            if changes_pulled and repo_type == 'nextjs':
                pm2_ids = repo.get('pm2_ids', [])
                build_command = repo.get('build_command', 'npm run build')
                if pm2_ids:
                    handle_nextjs_build(repo_path, pm2_ids, build_command)
        
        time.sleep(check_interval)

if __name__ == "__main__":
    logging.info("Starting Git Auto Pull Service")
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        daemonize()
    main()
