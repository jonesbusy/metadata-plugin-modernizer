import json
import os
import requests
import logging
from github import Github

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Authenticate with GitHub using GITHUB_TOKEN
token = os.getenv('GITHUB_TOKEN')
if not token:
    logging.error("GITHUB_TOKEN not found.")
    exit(1)

g = Github(token)

def update_pr_status(file_path):
    logging.info(f"Processing file: {file_path}")
    try:
        with open(file_path, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return

    pr_url = metadata.get('pullRequestUrl')
    if not pr_url:
        logging.warning(f"No pullRequestUrl found in {file_path}, skipping.")
        return

    try:
        parts = pr_url.split('/')
        owner, repo, pr_num = parts[3], parts[4], parts[6]
        logging.info(f"Extracted PR: {owner}/{repo}#{pr_num}")

        pr = g.get_repo(f"{owner}/{repo}").get_pull(int(pr_num))
        status = 'merged' if pr.merged else pr.state
        metadata['pullRequestStatus'] = status

        # Get Check Runs status
        commit = pr.base.repo.get_commit(pr.head.sha)
        check_runs = commit.get_check_runs()

        checks_summary = {check.name: check.conclusion for check in check_runs}
        metadata['checkRuns'] = checks_summary

        logging.info(f"Check runs for PR #{pr_num}: {checks_summary}")



        with open(file_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logging.info(f"Updated pullRequestStatus to '{status}' in {file_path}")

    except Exception as e:
        logging.error(f"Failed to update pullRequestStatus for {file_path}: {e}")

# Find all 'modernization-metadata' folders anywhere under root_dir
def find_all_metadata_dirs(root_dir='.'):
    matched_dirs = []
    for dirpath, dirnames, _ in os.walk(root_dir):
        for dirname in dirnames:
            if dirname == 'modernization-metadata':
                full_path = os.path.join(dirpath, dirname)
                matched_dirs.append(full_path)
    return matched_dirs

root_dir = '.'  # or your project root path
metadata_dirs = find_all_metadata_dirs(root_dir)

if not metadata_dirs:
    logging.error("No 'modernization-metadata' directories found.")
    exit(1)

logging.info(f"Found {len(metadata_dirs)} 'modernization-metadata' directories.")

for metadata_dir in metadata_dirs:
    logging.info(f"Processing directory: {metadata_dir}")
    for root, _, files in os.walk(metadata_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                update_pr_status(file_path)