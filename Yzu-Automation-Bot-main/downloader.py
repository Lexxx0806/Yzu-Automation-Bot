"""
School Portal File Downloader
------------------------------
Opens your school portal in a real browser window.
You log in manually, then the script finds and downloads
all course files (PDF, PPTX, DOCX, etc.) automatically.
"""

import asyncio
import json
import os
import re
import subprocess
import time
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

# ──────────────────────────────────────────────
# Load config
# ──────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config():
    if not CONFIG_FILE.exists():
        print("❌  config.json not found. Please make sure it's in the same folder.")
        input("Press Enter to exit...")
        exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
FILE_EXTENSIONS = [".pdf", ".pptx", ".ppt", ".docx", ".doc",
                   ".xlsx", ".xls", ".zip", ".mp4", ".png", ".jpg"]

def sanitize(name: str) -> str:
    """Remove characters that Windows doesn't allow in folder/file names."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def make_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path

def course_folder(base: Path, course_name: str) -> Path:
    return make_folder(base / sanitize(course_name))

def week_folder(course_path: Path, week_label: str) -> Path:
    return make_folder(course_path / sanitize(week_label))


# ──────────────────────────────────────────────
# GitHub push
# ──────────────────────────────────────────────
def run_git(args: list, cwd: Path) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return False, "Git is not installed or not in PATH."

def push_to_github(base_folder: Path, cfg: dict):
    repo_url    = cfg.get("github_repo_url", "").strip()
    branch      = cfg.get("github_branch", "main").strip() or "main"
    course_name = cfg.get("course_name", "My Course").strip()
    week_label  = cfg.get("week_label", "").strip()

    print("\n" + "="*55)
    print("  🐙  Pushing files to GitHub...")
    print("="*55)

    if not repo_url:
        print("❌  github_repo_url is not set in config.json. Skipping GitHub push.")
        return

    git_dir = base_folder / ".git"

    # Init repo if not already a git repo
    if not git_dir.exists():
        print("📦  Initialising new git repository...")
        ok, out = run_git(["init", "-b", branch], base_folder)
        if not ok:
            # older git versions don't support -b, try without
            run_git(["init"], base_folder)
            run_git(["checkout", "-b", branch], base_folder)

        # Write a .gitignore so we never accidentally commit secrets
        gitignore = base_folder / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*.log\n.DS_Store\nThumbs.db\n", encoding="utf-8")

        # Set remote
        ok, out = run_git(["remote", "add", "origin", repo_url], base_folder)
        if not ok:
            # remote might already exist
            run_git(["remote", "set-url", "origin", repo_url], base_folder)
        print(f"🔗  Remote set to: {repo_url}")
    else:
        # Make sure remote URL is up to date
        run_git(["remote", "set-url", "origin", repo_url], base_folder)

    # Add all new/changed files
    ok, out = run_git(["add", "-A"], base_folder)
    if not ok:
        print(f"❌  git add failed: {out}")
        return

    # Check if there's actually anything to commit
    ok2, status = run_git(["status", "--porcelain"], base_folder)
    if not status.strip():
        print("✅  Nothing new to commit — GitHub is already up to date.")
        return

    # Commit
    label_part = f" | {week_label}" if week_label else ""
    commit_msg = f"Add files: {course_name}{label_part}"
    ok, out = run_git(["commit", "-m", commit_msg], base_folder)
    if not ok:
        print(f"❌  git commit failed: {out}")
        return
    print(f"📝  Committed: \"{commit_msg}\"")

    # Push (set upstream on first push)
    print(f"🚀  Pushing to branch '{branch}'...")
    ok, out = run_git(["push", "-u", "origin", branch], base_folder)
    if ok:
        print(f"✅  Successfully pushed to GitHub!")
        print(f"    {repo_url}")
    else:
        print(f"❌  Push failed: {out}")
        print("\n💡  Common fixes:")
        print("    • Make sure you ran setup_github.bat and authenticated")
        print("    • Check that your repo URL in config.json is correct")
        print("    • Make sure the repo exists on GitHub (create it first!)")


# ──────────────────────────────────────────────
# Core downloader
# ──────────────────────────────────────────────
async def run():
    cfg = load_config()
    portal_url   = cfg.get("portal_url", "").strip()
    base_folder  = Path(cfg.get("download_folder", str(Path.home() / "Downloads" / "SchoolFiles")))
    course_name  = cfg.get("course_name", "My Course").strip()
    week_label   = cfg.get("week_label", "").strip()

    make_folder(base_folder)

    print("\n" + "="*55)
    print("  📚  School Portal File Downloader")
    print("="*55)
    print(f"  Portal  : {portal_url}")
    print(f"  Save to : {base_folder}")
    print("="*55)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(base_folder),
            args=["--start-maximized"]
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport=None
        )
        page = await context.new_page()

        # ── Step 1: Open portal ──────────────────────────
        print("\n🌐  Opening your school portal...")
        if portal_url:
            await page.goto(portal_url, wait_until="domcontentloaded")
        else:
            await page.goto("about:blank")
            print("⚠️   No portal URL set in config.json.")
            print("     Please type your portal URL in the browser address bar.")

        # ── Step 2: Wait for manual login ────────────────
        print("\n🔐  Please LOG IN in the browser window that just opened.")
        print("    Then NAVIGATE to the course or subject page you want to download from.")
        print("\n    ✅  When you're on the right page, come back here and press Enter.")
        input()

        # ── Step 3: Scan page for downloadable links ─────
        print("\n🔍  Scanning page for downloadable files...")
        current_url = page.url
        links = await page.eval_on_selector_all(
            "a[href]",
            """els => els.map(e => ({
                href: e.href,
                text: (e.innerText || e.getAttribute('aria-label') || e.getAttribute('title') || '').trim()
            }))"""
        )

        downloadable = []
        for link in links:
            href = link.get("href", "")
            text = link.get("text", "Unnamed File")
            parsed = urllib.parse.urlparse(href)
            ext = Path(parsed.path).suffix.lower()
            if ext in FILE_EXTENSIONS:
                downloadable.append({"href": href, "text": text or Path(parsed.path).name, "ext": ext})

        if not downloadable:
            print("\n⚠️   No direct file links found on this page.")
            print("     This can happen if your portal hides files behind buttons or iframes.")
            print("     Try navigating deeper into a specific course module, then press Enter to scan again.")
            input("     Press Enter to re-scan the current page...")
            links = await page.eval_on_selector_all(
                "a[href]",
                """els => els.map(e => ({
                    href: e.href,
                    text: (e.innerText || e.getAttribute('aria-label') || e.getAttribute('title') || '').trim()
                }))"""
            )
            for link in links:
                href = link.get("href", "")
                text = link.get("text", "Unnamed File")
                parsed = urllib.parse.urlparse(href)
                ext = Path(parsed.path).suffix.lower()
                if ext in FILE_EXTENSIONS:
                    downloadable.append({"href": href, "text": text or Path(parsed.path).name, "ext": ext})

        if not downloadable:
            print("\n❌  Still no files found. Your portal may require a different approach.")
            print("    See README.txt for tips on portals that hide files.")
            input("Press Enter to exit...")
            await browser.close()
            return

        print(f"\n📎  Found {len(downloadable)} file(s):")
        for i, d in enumerate(downloadable, 1):
            print(f"    [{i}] {d['text'][:60]}  ({d['ext']})")

        # ── Step 4: Set up save folder ───────────────────
        if week_label:
            save_path = week_folder(course_folder(base_folder, course_name), week_label)
        else:
            save_path = course_folder(base_folder, course_name)

        print(f"\n📁  Files will be saved to:\n    {save_path}\n")

        # ── Step 5: Download each file ───────────────────
        success, failed = 0, 0
        for item in downloadable:
            fname = sanitize(item["text"])
            if not fname.lower().endswith(item["ext"]):
                fname = fname + item["ext"]
            dest = save_path / fname

            # skip if already downloaded
            if dest.exists():
                print(f"  ⏭️   Already exists, skipping: {fname}")
                continue

            try:
                print(f"  ⬇️   Downloading: {fname}")
                async with context.expect_download(timeout=30_000) as dl_info:
                    await page.evaluate(f"window.open('{item['href']}', '_blank')")
                download = await dl_info.value
                await download.save_as(str(dest))
                print(f"  ✅  Saved: {fname}")
                success += 1
            except Exception as e:
                # Fallback: try direct navigation download
                try:
                    new_page = await context.new_page()
                    async with context.expect_download(timeout=30_000) as dl_info2:
                        await new_page.goto(item["href"])
                    download2 = await dl_info2.value
                    await download2.save_as(str(dest))
                    await new_page.close()
                    print(f"  ✅  Saved (alt method): {fname}")
                    success += 1
                except Exception as e2:
                    print(f"  ❌  Failed: {fname}  →  {str(e2)[:60]}")
                    failed += 1
            await asyncio.sleep(0.5)

        # ── Done ─────────────────────────────────────────
        print("\n" + "="*55)
        print(f"  ✅  Done!  {success} downloaded,  {failed} failed")
        print(f"  📁  Saved to: {save_path}")
        print("="*55)

        if failed > 0:
            print(f"\n⚠️   {failed} file(s) couldn't be downloaded automatically.")
            print("     These may require you to click them manually in the browser.")

        print("\n💡  NotebookLM tip:")
        print("    If your save folder is inside Google Drive for Desktop,")
        print("    open NotebookLM → New Notebook → Add Source → Google Drive")
        print("    and select the folder to import everything at once!\n")

        # ── GitHub push ──────────────────────────────────
        github_enabled = cfg.get("github_enabled", False)
        if github_enabled and success > 0:
            await asyncio.get_event_loop().run_in_executor(None, push_to_github, base_folder, cfg)

        input("Press Enter to close the browser and exit...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
