import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"--- {description} ---")
    result = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout)
        return True
    else:
        print(f"Error: {result.stderr}")
        return False

def sync():
    # 1. Fetch data from GitHub
    if not run_command(["scripts/fetch_progress.py"], "Fetching project data from GitHub"):
        return

    # 2. Generate project detail pages
    if not run_command(["scripts/generate_pages.py"], "Generating project detail pages"):
        return

    print("--- Sync Complete ---")
    print("Portfolio updated locally. View changes in your browser.")

if __name__ == "__main__":
    sync()
