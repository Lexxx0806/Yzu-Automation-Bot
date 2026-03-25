============================================================
  📚  SCHOOL PORTAL FILE DOWNLOADER — README
  Step-by-step guide for Windows (No coding needed!)
============================================================

──────────────────────────────────────────────────────────
  WHAT THIS DOES
──────────────────────────────────────────────────────────
This tool opens your school portal in a browser window.
You log in yourself (your password stays private — the
script never sees it). Then it automatically finds and
downloads all PDFs, PowerPoints, Word docs, and other
files from the page you're on, and organizes them into
folders on your laptop.


──────────────────────────────────────────────────────────
  FIRST TIME SETUP (do this once)
──────────────────────────────────────────────────────────

STEP 1 — Install Python
  a. Go to: https://www.python.org/downloads/
  b. Click the big "Download Python" button
  c. Run the installer
  ⚠️  IMPORTANT: On the first screen, check the box that says
     "Add python.exe to PATH" — this is easy to miss!
  d. Click "Install Now" and wait for it to finish

STEP 2 — Run setup.bat
  a. Find the folder where you saved this downloader
  b. Double-click "setup.bat"
  c. A black window will open and install everything
  d. Wait until it says "Setup complete!" then close it

STEP 3 — Edit config.json
  a. Right-click "config.json" → Open with → Notepad
  b. Fill in your details:

     "portal_url"       → Your school portal's web address
                          Example: "https://lms.myuniversity.edu"

     "download_folder"  → Where to save files on your laptop
                          Example: "C:/Users/John/Downloads/SchoolFiles"
                          (replace "John" with your Windows username —
                           check what's in C:\Users\ to find your name)

     "course_name"      → Name of the course you're downloading
                          Example: "Biology 101"

     "week_label"       → Optional: label for this batch of files
                          Example: "Week 3" or "Midterm Prep"
                          Leave it as "" if you don't want week folders

  c. Save the file (Ctrl+S) and close Notepad

──────────────────────────────────────────────────────────
  HOW TO USE (every time)
──────────────────────────────────────────────────────────

STEP 1 — Double-click "run.bat"
  A black window (command prompt) and a browser will open.

STEP 2 — Log in to your portal
  In the browser that opened, log in as you normally would.
  Then navigate to the course or module page with the files.

STEP 3 — Press Enter in the black window
  Once you're on the right page, click on the black window
  and press Enter. The script will scan and download everything.

STEP 4 — Wait for downloads to finish
  You'll see each file being downloaded. When done, press
  Enter again to close everything.


──────────────────────────────────────────────────────────
  YOUR FILES WILL BE ORGANIZED LIKE THIS
──────────────────────────────────────────────────────────

  SchoolFiles/
  ├── Biology 101/
  │   ├── Week 1/
  │   │   ├── Lecture_1_Intro_to_Cells.pdf
  │   │   └── Lab_Manual_Week1.docx
  │   ├── Week 2/
  │   │   ├── Chapter2_Slides.pptx
  │   │   └── Assignment_2.pdf
  │   └── Week 3/
  │       └── ...
  └── Chemistry/
      └── ...

  Just change "course_name" and "week_label" in config.json
  each time you run the script for a different course/week!


──────────────────────────────────────────────────────────
  🐙  GITHUB SETUP (auto-push files to a GitHub repo)
──────────────────────────────────────────────────────────

After every download session, the script can automatically
commit and push all new files to a GitHub repository.

HOW TO SET IT UP (one time only):

STEP 1 — Create a GitHub account (if you don't have one)
  Go to https://github.com and sign up for free.

STEP 2 — Create a new empty repository
  a. Log in to GitHub
  b. Click the "+" icon (top right) → "New repository"
  c. Name it something like: school-files
  d. Set it to Private (recommended for school materials)
  e. Click "Create repository"
  f. Copy the repo URL — it looks like:
     https://github.com/YourUsername/school-files

STEP 3 — Run setup_github.bat
  Double-click "setup_github.bat" in the downloader folder.
  It will:
    • Check if Git is installed (and tell you how to install it)
    • Ask for your name and GitHub email
    • Log you into GitHub (opens a browser window)

STEP 4 — Update config.json
  Open config.json in Notepad and set:
    "github_enabled": true,
    "github_repo_url": "https://github.com/YourUsername/school-files",
    "github_branch": "main"

That's it! Now every time you run run.bat, it will
download your files AND push them to GitHub automatically.

YOUR GITHUB REPO WILL LOOK LIKE THIS:
  school-files/
  ├── Biology 101/
  │   ├── Week 1/
  │   │   ├── Lecture_1_Intro_to_Cells.pdf
  │   │   └── Lab_Manual_Week1.docx
  │   └── Week 2/
  │       └── Chapter2_Slides.pptx
  └── Chemistry/
      └── ...

ALTERNATIVE: Personal Access Token (if setup_github.bat fails)
  a. Go to: https://github.com/settings/tokens
  b. Click "Generate new token (classic)"
  c. Check the "repo" scope
  d. Copy the token
  e. When git asks for a password, paste the token there
     (your real password won't work — always use the token)

──────────────────────────────────────────────────────────
  📓  NOTEBOOKLM SETUP (to use files in Google NotebookLM)
──────────────────────────────────────────────────────────

The easiest way to get files into NotebookLM is to save
them directly inside your Google Drive folder:

OPTION A — Save directly to Google Drive (Recommended)
  1. Install "Google Drive for Desktop":
     https://www.google.com/drive/download/
  2. After installing, you'll have a Google Drive folder,
     usually at: C:/Users/YourName/Google Drive/My Drive/
  3. Set your "download_folder" in config.json to something
     like: "C:/Users/John/Google Drive/My Drive/SchoolFiles"
  4. Files download straight into Drive — they auto-sync!
  5. In NotebookLM: New Notebook → Add Source → Google Drive
     → find your SchoolFiles folder → done! 🎉

OPTION B — Upload manually
  1. Download files to your laptop as normal
  2. Go to https://notebooklm.google.com
  3. Create a new Notebook for each course
  4. Click "Add Source" → Upload files
  5. Select all the files from your course folder


──────────────────────────────────────────────────────────
  🔧  TROUBLESHOOTING
──────────────────────────────────────────────────────────

"Python not found" error
  → You didn't check "Add Python to PATH" during install.
    Uninstall Python and reinstall, making sure to check that box.

"No files found on this page"
  → Your portal might hide files inside a module or section.
    Click into a specific week/module on your portal, THEN press Enter.
  → Some portals use special download buttons instead of links.
    In this case, you'll need to download files manually from the
    browser, but the folder organization still works!

Files download but have wrong names
  → Edit config.json and set better "course_name" and "week_label"
    values. Re-run the script (it will skip already downloaded files).

Browser closes immediately
  → Check that config.json is saved properly and has no typos.
    Open it in Notepad and make sure all quotes are straight (" ")
    not curly (" ").

Script downloads the same files again
  → It won't! The script checks if a file already exists and skips it.

"I need to download files from multiple courses"
  → Just change "course_name" and "week_label" in config.json
    and run run.bat again for each course/week. Easy!


──────────────────────────────────────────────────────────
  📋  QUICK REFERENCE — config.json CHEAT SHEET
──────────────────────────────────────────────────────────

{
    "portal_url": "https://lms.myuniversity.edu",
    "download_folder": "C:/Users/YourName/Downloads/SchoolFiles",
    "course_name": "Biology 101",
    "week_label": "Week 3"
}

  • Always use forward slashes (/) in folder paths, not backslash (\)
  • Always keep the quotes around values
  • Change course_name and week_label each time you run


──────────────────────────────────────────────────────────
  Made with ❤️  — Good luck with your studies!
──────────────────────────────────────────────────────────
