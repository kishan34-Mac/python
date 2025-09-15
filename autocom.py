import subprocess
import datetime
import schedule
import time
import os

# ✅ List of repo folders
REPO_PATHS = [
    "/Users/kishan/Desktop/todo",
    "/Users/kishan/Desktop/Ai Quiz",
    "/Users/kishan/Desktop/Ai code reviwer",
    "/Users/kishan/Desktop/nova-mart-bloom-main"
]

def git_auto_commit(repo_path):
    try:
        # ✅ Create/Update heartbeat.txt in each repo
        heartbeat_file = os.path.join(repo_path, "heartbeat.txt")
        with open(heartbeat_file, "a") as f:
            f.write(f"Updated at {datetime.datetime.now()}\n")

        commit_message = f"Auto commit at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Detect current branch dynamically
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()

        # Run git commands
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True)
        subprocess.run(["git", "push", "origin", branch], cwd=repo_path, check=True)

        print(f"✅ [{repo_path}] Auto commit & push successful → {commit_message}")
    except subprocess.CalledProcessError:
        print(f"ℹ️ [{repo_path}] Nothing to commit or error occurred")

def auto_commit_all():
    for path in REPO_PATHS:
        git_auto_commit(path)

# ✅ Schedule every 1 minute
schedule.every(5).minutes.do(auto_commit_all)

print(f"⏳ Auto commit scheduler started for {len(REPO_PATHS)} repos...")

while True:
    schedule.run_pending()
    time.sleep(1)
