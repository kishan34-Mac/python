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
GIT_USER_EMAIL = "jsmith80769@gmail.com"  # Linked to GitHub account: kishan34-Mac
GITHUB_USERNAME = "kishan34-Mac"

REPO_PATHS = [
    "/Users/kishan/Desktop/Insta-Dm 2",
]

INTERVAL = 300  # 5 min interval for loop mode

# Default commit range per execution / batch: 5 to 10 commits
DEFAULT_MIN_COMMITS = 5
DEFAULT_MAX_COMMITS = 10

LEVEL_COMMITS = {
    1: (1, 3),       # Light Green (1-3 commits)
    2: (4, 6),       # Medium Green (4-6 commits)
    3: (7, 9),       # Dark Green (7-9 commits)
    4: (5, 10),      # Default batch (5-10 commits)
}

DEFAULT_LEVEL = 4  # Default to 5-10 commits

COMMIT_MESSAGES = [
    "⚡ update progress and logs",
    "📝 docs: update daily progress tracking",
    "🔧 refactor: internal code updates",
    "✨ feat: sync recent updates",
    "🐛 fix: minor adjustments and tweaks",
    "🚀 chore: update build and activity log"
]

# ---------------------------------------- #

def log(msg):
    now = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def run(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
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

def update_activity_file(repo, commit_num):
    progress_file = Path(repo) / "progress.md"
    activity_file = Path(repo) / "activity.txt"
    
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    with progress_file.open("a", encoding="utf-8") as f:
        f.write(f"- Activity log update #{commit_num} at {timestamp}\n")

    with activity_file.open("a", encoding="utf-8") as f:
        f.write(f"Commit #{commit_num} - {timestamp}\n")

    return [progress_file, activity_file]

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
                3: "Level 3 (Dark Green)",
                4: "Level 4 (Darkest Green 🔥)"
            }
            log(f"📊 Live GitHub Status for Today ({today}):")
            log(f"   • Tooltip: {tooltip}")
            log(f"   • Color:   {level_names.get(level, f'Level {level}')}")

            if level == 0:
                log("   ⏳ Note: GitHub's background worker is still processing your pushed commits.")
                log("      Contributions usually take 5–20 minutes to reflect on the profile graph.")
                log("      Tip: Hard refresh your browser with Cmd + Shift + R (Mac) or Ctrl + F5 (Win).")
            else:
                log(f"   ✅ Contribution registered on GitHub! ({tooltip})")
            return level, tooltip
        else:
            log(f"ℹ️ Today ({today}) was not found in the GitHub calendar fragment.")
    except Exception as e:
        log(f"⚠️ Could not check live GitHub status ({e})")
    return None, None

def process_repo(repo, target_commits=None, level=DEFAULT_LEVEL, min_commits=DEFAULT_MIN_COMMITS, max_commits=DEFAULT_MAX_COMMITS):
    if not os.path.isdir(repo):
        log(f"❌ Invalid repo path: {repo}")
        return 0

    log(f"📁 Processing repo: {repo}")

    setup_git(repo)

    # 1. Recover from any unfinished rebase/merge from previous interrupted runs
    git_dir = Path(repo) / ".git"
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        log("⚠️ Found unfinished rebase in progress. Aborting it to restore clean state...")
        run(["git", "rebase", "--abort"], repo)
    if (git_dir / "MERGE_HEAD").exists():
        log("⚠️ Found unfinished merge in progress. Aborting it to restore clean state...")
        run(["git", "merge", "--abort"], repo)

    # 2. Switch to main branch
    checkout_res = run(["git", "checkout", "main"], repo)
    if checkout_res.returncode != 0:
        log(f"❌ Failed to switch to branch 'main': {checkout_res.stderr.strip() or checkout_res.stdout.strip()}")
        return 0

    # 3. Fetch and sync with origin/main
    fetch_res = run(["git", "fetch", "origin", "main"], repo)
    if fetch_res.returncode != 0:
        log(f"⚠️ Fetch warning: {fetch_res.stderr.strip() or fetch_res.stdout.strip()}")

    # Try clean pull --rebase
    pull_res = run(["git", "pull", "--rebase", "origin", "main"], repo)
    if pull_res.returncode != 0:
        log("⚠️ git pull --rebase encountered conflicts. Aborting rebase...")
        run(["git", "rebase", "--abort"], repo)
        log("🔄 Resetting local main to origin/main to eliminate divergence...")
        reset_res = run(["git", "reset", "--hard", "origin/main"], repo)
        if reset_res.returncode != 0:
            log(f"❌ Failed to reset to origin/main: {reset_res.stderr.strip()}")
            return 0

    # Determine commit count (5 to 10 commits by default)
    if target_commits is not None:
        commits_count = target_commits
    elif min_commits != DEFAULT_MIN_COMMITS or max_commits != DEFAULT_MAX_COMMITS:
        commits_count = random.randint(min_commits, max_commits)
    else:
        min_c, max_c = LEVEL_COMMITS.get(level, (DEFAULT_MIN_COMMITS, DEFAULT_MAX_COMMITS))
        commits_count = random.randint(min_c, max_c)

    log(f"🔥 Stage & Commit: Generating {commits_count} commits (Batch: {commits_count} commits)...")

    start_num = get_last_commit_num(repo)
    successful_commits = 0
    start_time = time.time()

    for i in range(1, commits_count + 1):
        commit_id = start_num + i
        update_activity_file(repo, commit_id)
        run(["git", "add", "progress.md", "activity.txt"], repo)

        msg = f"{random.choice(COMMIT_MESSAGES)} (#{commit_id})"
        commit_res = run(["git", "commit", "-m", msg], repo)

        if commit_res.returncode == 0:
            successful_commits += 1
        time.sleep(0.3)

    elapsed = round(time.time() - start_time, 2)
    log(f"⚡ {successful_commits}/{commits_count} commits registered & staged in {elapsed}s.")

    # 📤 Single push to GitHub
    log("📤 Pushing commits to GitHub remote (origin main)...")
    push_res = run(["git", "push", "origin", "main"], repo)
    
    if push_res.returncode == 0:
        log(f"✅ SUCCESS! {successful_commits} commits successfully pushed to origin/main! 🚀")
        return successful_commits
    else:
        log(f"❌ Push failed: {push_res.stderr.strip()}")
        return 0

def run_target_dark(repo, min_commits=DEFAULT_MIN_COMMITS, max_commits=DEFAULT_MAX_COMMITS, delay_between_batches=2):
    """
    Gradually pushes commits in small batches of 5-10 commits with delays
    until the GitHub Dark Green threshold (~295 commits) is reached.
    This avoids dumping 300 commits all at once in one single burst.
    """
    TARGET_COMMITS_FOR_DARK = 295
    already_done = get_today_commits_count(repo)
    needed = max(0, TARGET_COMMITS_FOR_DARK - already_done)

    log(f"🎯 Target Dark Mode Activated: Need ~{TARGET_COMMITS_FOR_DARK} commits for Level 4 Dark Green.")
    log(f"   • Commits already present today: {already_done}")
    log(f"   • Remaining commits to generate: {needed}")

    if needed == 0:
        log("🎉 Already reached threshold for Dark Green today!")
        return

    total_pushed = 0
    batch_num = 1

    while total_pushed < needed:
        batch_size = random.randint(min_commits, max_commits)
        batch_size = min(batch_size, needed - total_pushed)
        log(f"\n📦 [Batch #{batch_num}] Generating {batch_size} commits ({total_pushed}/{needed} completed)...")

        pushed = process_repo(repo, target_commits=batch_size)
        if pushed == 0:
            log("⚠️ Push encountered an issue, stopping batch loop.")
            break

        total_pushed += pushed
        batch_num += 1

        if total_pushed < needed:
            log(f"⏳ Cooling down for {delay_between_batches}s before next 5-10 commit batch...")
            time.sleep(delay_between_batches)

    log(f"\n🎉 Finished! Successfully generated & pushed {total_pushed} commits in safe 5-10 commit batches.")

def main():
    parser = argparse.ArgumentParser(description="GitHub Contribution Graph Automation Tool")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4], default=DEFAULT_LEVEL,
                        help="Target commit level (default Level 4: 5-10 commits)")
    parser.add_argument("--commits", type=int, default=None,
                        help="Exact number of commits to generate (overrides 5-10 default)")
    parser.add_argument("--min-commits", type=int, default=DEFAULT_MIN_COMMITS,
                        help="Minimum commits per batch (default: 5)")
    parser.add_argument("--max-commits", type=int, default=DEFAULT_MAX_COMMITS,
                        help="Maximum commits per batch (default: 10)")
    parser.add_argument("--target-dark", action="store_true",
                        help="Gradually push in batches of 5-10 commits until GitHub Dark Green threshold (~295) is reached")
    parser.add_argument("--check", action="store_true",
                        help="Check live GitHub graph status without generating commits")
    parser.add_argument("--loop", action="store_true",
                        help="Run continuously in a loop every 5 minutes, doing 5-10 commits each time")
    parser.add_argument("--interval", type=int, default=INTERVAL,
                        help="Interval in seconds for loop mode (default: 300s / 5 mins)")

    args = parser.parse_args()

    log("🚀 GitHub Contribution Graph Automation Tool")
    log(f"Configured Email:    {GIT_USER_EMAIL}")
    log(f"Configured Name:     {GIT_USER_NAME}")
    log(f"GitHub Profile:      https://github.com/{GITHUB_USERNAME}")

    if args.check:
        check_github_graph_status(GITHUB_USERNAME)
        return

    if args.target_dark:
        for repo in REPO_PATHS:
            run_target_dark(repo, min_commits=args.min_commits, max_commits=args.max_commits)
        check_github_graph_status(GITHUB_USERNAME)
        return

    is_loop = args.loop
    interval = args.interval

    while True:
        for repo in REPO_PATHS:
            process_repo(
                repo,
                target_commits=args.commits,
                level=args.level,
                min_commits=args.min_commits,
                max_commits=args.max_commits
            )

        # Check live graph status
        check_github_graph_status(GITHUB_USERNAME)

        if not is_loop:
            log("🎉 Process finished.")
            break

        log(f"😴 Sleeping for {interval} seconds...\n")
        time.sleep(interval)

if __name__ == "__main__":
    main()