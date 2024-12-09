import os
import time
import subprocess
import logging
from datetime import datetime
import yaml

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

def main():
    config = load_config()
    check_interval = config.get('check_interval', 300)  # Default 5 minutes
    
    while True:
        for repo in config['repositories']:
            repo_path = repo['path']
            branch = repo['branch']
            
            logging.info(f"Checking repository: {repo_path} on branch {branch}")
            git_pull(repo_path, branch)
        
        time.sleep(check_interval)

if __name__ == "__main__":
    logging.info("Starting Git Auto Pull Service")
    main()