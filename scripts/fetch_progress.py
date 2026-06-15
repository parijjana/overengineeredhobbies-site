import urllib.request
import re
import json
import os

# Configuration: Repositories to track progress for
REPOS = [
    "GASTROTATOR_ANDROID",
    "AULOS",
    "KALKRA",
    "pellucid",
    "contexthistory",
    "lore",
    "thesign"
]

USER = "parijjana"
BASE_URL = "https://raw.githubusercontent.com/{user}/{repo}/main/FEATURE_TRACKER.md"
OUTPUT_FILE = "assets/progress.json"

def fetch_and_parse(repo):
    url = BASE_URL.format(user=USER, repo=repo)
    print(f"Fetching {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            
            # Count [x] and [ ]
            # Using regex to find markdown task list patterns
            implemented = len(re.findall(r'-\s+\[x\]', content, re.IGNORECASE))
            planned = len(re.findall(r'-\s+\[\s\]', content, re.IGNORECASE))
            
            total = implemented + planned
            percentage = round((implemented / total * 100), 1) if total > 0 else 0
            
            return {
                "implemented": implemented,
                "planned": planned,
                "total": total,
                "percentage": percentage,
                "status": "success"
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Warning: FEATURE_TRACKER.md not found for {repo}")
            return {"status": "not_found"}
        else:
            print(f"Error fetching {repo}: {e}")
            return {"status": "error", "message": str(e)}
    except Exception as e:
        print(f"Unexpected error for {repo}: {e}")
        return {"status": "error", "message": str(e)}

def main():
    # Ensure assets directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    results = {}
    for repo in REPOS:
        results[repo] = fetch_and_parse(repo)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Progress data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
