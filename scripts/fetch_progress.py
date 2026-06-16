import urllib.request
import re
import json
import os
import sys

# ── CONFIGURATION ──────────────────────────────────────────────────────────
# Add the exact repository names you want to track here.
# The script will only attempt to fetch FEATURE_TRACKER.md for these repos.
REPOS = [
    "lore",
    "thesign",
    "contexthistory",
    "pellucid",
    "KALKRA",
    "AULOS",
    "GASTROTATOR_ANDROID"
]

USER = "parijjana"
BASE_URL = "https://raw.githubusercontent.com/{user}/{repo}/main/FEATURE_TRACKER.md"
OUTPUT_FILE = "assets/progress.json"
TIMEOUT = 10 # Seconds

# ────────────────────────────────────────────────────────────────────────────

def fetch_and_parse(repo):
    url = BASE_URL.format(user=USER, repo=repo)
    print(f"Fetching {repo} roadmap...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            content = response.read().decode('utf-8')
            
            # Count [x] and [ ]
            # Patterns: "- [x]", "- [X]", "- [ ]"
            implemented = len(re.findall(r'-\s+\[x\]', content, re.IGNORECASE))
            planned = len(re.findall(r'-\s+\[\s\]', content, re.IGNORECASE))
            
            total = implemented + planned
            if total == 0:
                print(f"  ! Found FEATURE_TRACKER.md for {repo} but no features defined.")
                return None
                
            percentage = round((implemented / total * 100), 1)
            
            print(f"  + Success: {implemented}/{total} features tracked.")
            return {
                "implemented": implemented,
                "planned": planned,
                "total": total,
                "percentage": percentage,
                "status": "success"
            }
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  - Skipping {repo}: FEATURE_TRACKER.md not found.")
        else:
            print(f"  - Error fetching {repo} (HTTP {e.code}): {e.reason}")
        return None
    except Exception as e:
        print(f"  - Unexpected error for {repo}: {e}")
        return None

def main():
    # Use CLI arguments if provided, otherwise use the default REPOS list
    target_repos = sys.argv[1:] if len(sys.argv) > 1 else REPOS
    
    if not target_repos:
        print("No repositories specified. Please provide repo names as arguments or update REPOS in the script.")
        return

    # Ensure assets directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    results = {}
    print(f"Starting progress synchronization for {USER}...")
    
    for repo in target_repos:
        data = fetch_and_parse(repo)
        if data:
            results[repo] = data
    
    # Save the successful results
    if results:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDone! Progress data for {len(results)} projects saved to {OUTPUT_FILE}")
    else:
        print("\nNo progress data fetched. Output file not updated.")

if __name__ == "__main__":
    main()
