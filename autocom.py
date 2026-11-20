import subprocess
import datetime as dt
import time
import os
import sys
from pathlib import Path
import random
import argparse
import urllib.request
import ssl
import re

# ---------------- CONFIG ---------------- #

GIT_USER_NAME = "Kishan Singh"
GIT_USER_EMAIL = "jsmith80769@gmail.com"  # Verified GitHub email for kishan34-Mac
GITHUB_USERNAME = "kishan34-Mac"

# Target repositories to maintain daily activity
REPO_PATHS = [
    "/Users/kishan/Desktop/Insta-Dm 2",
]

# Set default commits to 5 - 6 commits per run
DEFAULT_MIN_COMMITS = 5
DEFAULT_MAX_COMMITS = 6

COMMIT_MESSAGES = [
    "✨ feat: update core logic and daily modules",
    "📝 docs: update daily progress tracking",
    "🔧 refactor: improve internal code structure",
    "🐛 fix: minor adjustments and tweaks",
    "🚀 chore: update project build and sync logs",
    "♻️ refactor: optimize component routines",
    "📈 perf: improve processing efficiency"
]

INTERVAL = 300  # 5 min interval for loop mode

# ---------------------------------------- #

def log(msg):
    now = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def run(cmd, cwd, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=merged_env)
    if res.returncode != 0 and "nothing to commit" not in res.stdout:
        log(f"⚠️ Git Notice ({' '.join(cmd)}): {res.stderr.strip() or res.stdout.strip()}")
    return res

def setup_git(repo):
    run(["git", "config", "user.name", GIT_USER_NAME], repo)
    run(["git", "config", "user.email", GIT_USER_EMAIL], repo)

def get_last_commit_num(repo):
    activity_file = Path(repo) / "activity.txt"
    if not activity_file.exists():
        return 0
    try:
        with activity_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            match = re.search(r"Commit #(\d+)", line)
            if match:
                return int(match.group(1))
    except Exception:
        pass
    return 0

def get_today_commits_count(repo):
    today = dt.datetime.now().strftime("%Y-%m-%d")
    res = subprocess.run(
        ["git", "log", f"--since={today} 00:00:00", "--oneline"],
        cwd=repo, text=True, capture_output=True
    )
    if res.returncode == 0 and res.stdout.strip():
        return len(res.stdout.strip().splitlines())
    return 0

def update_activity_file(repo, commit_num, timestamp_str):
    progress_file = Path(repo) / "progress.md"
    activity_file = Path(repo) / "activity.txt"

    with progress_file.open("a", encoding="utf-8") as f:
        f.write(f"- Activity log update #{commit_num} at {timestamp_str}\n")

    with activity_file.open("a", encoding="utf-8") as f:
        f.write(f"Commit #{commit_num} - {timestamp_str}\n")

def check_github_graph_status(username=GITHUB_USERNAME):
    log(f"🔍 Checking live GitHub Contribution Graph for @{username}...")
    try:
        ctx = ssl._create_unverified_context()
        url = f"https://github.com/users/{username}/contributions?cb={int(time.time())}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode("utf-8")

        today = dt.datetime.now().strftime("%Y-%m-%d")
        match = re.search(
            r'<td[^>]*data-date="' + today + r'"[^>]*data-level="(\d+)"[^>]*></td>\s*<tool-tip[^>]*>([^<]+)</tool-tip>',
            html
        )
        if match:
            level = int(match.group(1))
            tooltip = match.group(2).strip()
            level_names = {
                0: "Level 0 (No Green / Gray)",
                1: "Level 1 (Light Green)",
                2: "Level 2 (Medium Green)",
                3: "Level 3 (Deep Green)",
                4: "Level 4 (Darkest Green 🔥)"
            }
            log(f"📊 Live GitHub Status for Today ({today}):")
            log(f"   • Tooltip: {tooltip}")
            log(f"   • Level:   {level_names.get(level, f'Level {level}')}")

            if level > 0:
                log(f"   🟢 Activity recorded on GitHub! ({tooltip})")
            else:
                log("   ⏳ Note: GitHub's background worker processes newly pushed commits within 5–10 mins.")
                log("      Tip: Hard refresh your profile with Cmd + Shift + R (Mac) or Ctrl + F5 (Win).")
            return level, tooltip
        else:
            log(f"ℹ️ Today ({today}) was not found in the GitHub calendar fragment.")
    except Exception as e:
        log(f"⚠️ Could not check live GitHub status ({e})")
    return None, None

def process_repo(repo, num_commits=None):
    """
    Generates exactly 5-6 clean, realistic commits and pushes cleanly to origin/main.
    """
    if not os.path.isdir(repo):
        log(f"❌ Invalid repo path: {repo}")
        return 0

    log(f"📁 Processing repo: {repo}")
    setup_git(repo)

    # 1. Recover from any unfinished rebase/merge
    git_dir = Path(repo) / ".git"
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        log("⚠️ Found unfinished rebase. Aborting it...")
        run(["git", "rebase", "--abort"], repo)
    if (git_dir / "MERGE_HEAD").exists():
        log("⚠️ Found unfinished merge. Aborting it...")
        run(["git", "merge", "--abort"], repo)

    # 2. Switch to main branch
    checkout_res = run(["git", "checkout", "main"], repo)
    if checkout_res.returncode != 0:
        log(f"❌ Failed to switch to branch 'main': {checkout_res.stderr.strip() or checkout_res.stdout.strip()}")
        return 0

    # 3. Sync with remote main
    log("🔄 Syncing with remote origin/main...")
    run(["git", "fetch", "origin", "main"], repo)
    pull_res = run(["git", "pull", "--rebase", "origin", "main"], repo)
    if pull_res.returncode != 0:
        log("⚠️ Pull conflict encountered. Resetting to origin/main...")
        run(["git", "rebase", "--abort"], repo)
        run(["git", "reset", "--hard", "origin/main"], repo)

    # 4. Determine commit count (5 to 6 commits by default)
    if num_commits is not None:
        commits_to_create = num_commits
    else:
        commits_to_create = random.randint(DEFAULT_MIN_COMMITS, DEFAULT_MAX_COMMITS)

    today_count = get_today_commits_count(repo)
    today_str = dt.datetime.now().strftime("%Y-%m-%d")
    log(f"📅 Today ({today_str}) existing commits: {today_count}")
    log(f"⚡ Generating exactly {commits_to_create} quality commits...")

    start_num = get_last_commit_num(repo)
    start_time = time.time()
    now = dt.datetime.now()
    successful_commits = 0

    for i in range(1, commits_to_create + 1):
        commit_id = start_num + i

        # Natural distributed timestamps spaced by 15-30 seconds
        seconds_offset = (commits_to_create - i) * 20
        commit_dt = now - dt.timedelta(seconds=seconds_offset)
        timestamp_str = commit_dt.strftime("%Y-%m-%d %H:%M:%S")
        iso_date = commit_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

        update_activity_file(repo, commit_id, timestamp_str)
        run(["git", "add", "progress.md", "activity.txt"], repo)

        msg = f"{random.choice(COMMIT_MESSAGES)} (#{commit_id})"

        env_dates = {
            "GIT_AUTHOR_DATE": iso_date,
            "GIT_COMMITTER_DATE": iso_date
        }
        commit_res = run(["git", "commit", "-m", msg], repo, env=env_dates)
        if commit_res.returncode == 0:
            successful_commits += 1

    # Single push to GitHub
    log(f"📤 Pushing {successful_commits} commits to origin/main...")
    push_res = run(["git", "push", "origin", "main"], repo)
    elapsed = round(time.time() - start_time, 2)

    if push_res.returncode == 0:
        log(f"✅ SUCCESS! Generated & pushed {successful_commits} commits in {elapsed}s! 🚀")
        return successful_commits
    else:
        log(f"❌ Push failed: {push_res.stderr.strip()}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="GitHub Activity Automation (5-6 Quality Commits)")
    parser.add_argument("--commits", type=int, default=None,
                        help="Exact number of commits to generate (default: 5-6)")
    parser.add_argument("--check", action="store_true",
                        help="Check live GitHub contribution graph status without generating commits")
    parser.add_argument("--loop", action="store_true",
                        help="Run continuously every interval (default: 5 min)")
    parser.add_argument("--interval", type=int, default=INTERVAL,
                        help="Interval in seconds for loop mode (default: 300s)")

    args = parser.parse_args()

    log("🚀 GitHub Contribution Graph Tool (Safe 5-6 Commits)")
    log(f"Author Email:    {GIT_USER_EMAIL}")
    log(f"Author Name:     {GIT_USER_NAME}")
    log(f"GitHub Profile:  https://github.com/{GITHUB_USERNAME}")

    if args.check:
        check_github_graph_status(GITHUB_USERNAME)
        return

    while True:
        for repo in REPO_PATHS:
            process_repo(repo, num_commits=args.commits)

        # Check live graph status
        check_github_graph_status(GITHUB_USERNAME)

        if not args.loop:
            log("🎉 Finished. Check your profile at https://github.com/" + GITHUB_USERNAME)
            break

        log(f"😴 Sleeping for {args.interval} seconds...\n")
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
