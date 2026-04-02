# YZU Portal File Downloader

An automated tool that logs into the YZU (Yuan Ze University) Portal and downloads all course files (PDFs, PowerPoints, Word docs, and more) — organized into folders on your laptop and optionally pushed to GitHub.

Built by a YZU student, for YZU students. Contributions welcome!

---

## Features

- Auto-login to the YZU portal
- Switches portal to English automatically
- **Auto-discovers all your courses** — no manual setup needed
- Downloads files from all courses at once
- Organizes files into folders by course name
- Skips files you've already downloaded
- Detects and replaces updated files (when a professor re-uploads the same file)
- Cleans up UUID junk temp files automatically
- Downloads multiple courses and files concurrently
- Auto-pushes new files to a GitHub repo (optional)
- Tracks downloaded files via `downloaded_files.json` so nothing is missed

---

## Requirements

- Windows 10/11 or macOS
- Python 3.10+
  - **Windows:** check **"Add Python to PATH"** during install
  - **macOS:** install from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python`)
- Git (only needed for the GitHub push feature)

---

## Setup (First Time Only)

### Step 1 — Clone or download this repo
```bash
git clone https://github.com/Lexxx0806/Yzu-Automation-Bot.git
cd Yzu-Automation-Bot
```
Or click the green **Code** button → **Download ZIP** and extract it.

---

### Step 2 — Install dependencies

**Windows** — double-click `setup.bat`, or run in a terminal:
```bash
pip install playwright python-dotenv
python -m playwright install chromium
```

**macOS** — run in a terminal:
```bash
bash setup.sh
```
Or manually:
```bash
pip3 install playwright python-dotenv
python3 -m playwright install chromium
```

---

### Step 3 — Create your `.env` file
Create a file called `.env` in the project folder (same folder as `downloader.py`):
```
YZU_USERNAME=your_student_id
YZU_PASSWORD=your_password
```
> Never share this file or commit it to GitHub. It's already in `.gitignore` so it won't be uploaded automatically.

---

### Step 4 — Edit `config.json`
```json
{
    "portal_url": "https://portalx.yzu.edu.tw/PortalSocialVB/Login.aspx",
    "download_folder": "",
    "github_enabled": false,
    "github_repo_url": "",
    "github_branch": "main"
}
```
- Leave `download_folder` as `""` to use the default save location (`~/Downloads/School Files`)
- Or set a custom path:
  - **Windows:** `"C:/Users/YourName/OneDrive/Desktop/School Files"`
  - **macOS:** `"/Users/YourName/Desktop/School Files"`

> **Windows 11 tip:** If your Desktop is inside OneDrive, make sure the path includes `OneDrive/Desktop`.

---

That's it. No need to manually find or enter course IDs — the bot reads your courses directly from the portal sidebar after login.

---

## Running the Downloader

**Windows** — double-click `run.bat`, or:
```bash
python downloader.py
```

**macOS** — run in a terminal:
```bash
bash run.sh
```
Or:
```bash
python3 downloader.py
```

The script will:
1. Open a browser and log in automatically
2. Switch the portal to English
3. Auto-discover all your enrolled courses from the sidebar
4. Scan every course concurrently for new or updated files
5. Download only what's new or has been updated by a professor
6. Organize everything into folders by course name
7. Clean up any UUID junk files left behind
8. Push to GitHub (if enabled)

---

## How File Tracking Works

The script keeps a `downloaded_files.json` file that remembers every file it has downloaded and its `AttachmentID`. On each run:

| Situation | What happens |
|---|---|
| File doesn't exist | `[DOWN]` — downloads it |
| File exists, same AttachmentID | `[SKIP]` — already up to date |
| File exists, new AttachmentID | `[UPDATE]` — replaces old file with professor's newer version |
| File was accidentally deleted | `[DOWN]` — re-downloads it automatically |

---

## Folder Structure

```
School Files/
├── Introduction to Algorithms/
│   ├── asymptotic analysis-1.pptx
│   └── Lecture 1 - Introduction to Algorithms.pdf
├── Machine Learning/
│   ├── linear perceptron links.pptx
│   └── 04 linear classification perceptron.pdf
├── Information Privacy/
│   └── 20260316 Social Networks.pdf
├── Assembly Language and Computer Organization/
│   └── chapter_01 - rb.pdf
└── ...
```

---

## GitHub Auto-Push (Optional)

To have files automatically pushed to a GitHub repo after each download:

1. Create a new private repository on GitHub
2. In `config.json`, set:
```json
"github_enabled": true,
"github_repo_url": "https://github.com/YourUsername/your-repo.git",
"github_branch": "main"
```
3. Initialize git in the project folder:

**Windows:**
```bash
cd "C:/Users/YourName/OneDrive/Desktop/Yzu-Automation-Bot"
git init -b main
git remote add origin https://github.com/YourUsername/your-repo.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

**macOS:**
```bash
cd ~/Desktop/Yzu-Automation-Bot
git init -b main
git remote add origin https://github.com/YourUsername/your-repo.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

After that, every time the downloader finds new files, they will be committed and pushed automatically.

> **GitHub password tip:** GitHub no longer accepts your account password for `git push`. Use a **Personal Access Token** instead.
> Go to: `GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate new token` with `repo` scope.

---

## Troubleshooting

**"No module named playwright"**
Run `pip install playwright` then install Chromium:
```bash
python -m playwright install chromium      # Windows
python3 -m playwright install chromium     # macOS
```

**Login fails**
Make sure your `.env` file has the correct student ID and password. Try logging into the portal manually to verify your credentials.

**Course auto-discovery finds no courses**
The bot falls back to the hardcoded `COURSES` dictionary in `downloader.py`. You can add your courses there manually as a fallback:
```python
COURSES = {
    "32440": "Introduction to Algorithms",
    "31221": "Introduction to Operating System",
}
```
To find a PageID: log in, click a course in the sidebar, and look at the URL — it will contain `PageID=XXXXX`.

**Files not saving to the right place**
Leave `download_folder` empty in `config.json` to use the default (`~/Downloads/School Files`). If setting a custom path on Windows 11, your Desktop is often inside OneDrive — use `C:/Users/YourName/OneDrive/Desktop/School Files`.

**Script only downloads some files from a course**
The portal may have been slow. Just run the script again — it will skip already-downloaded files and pick up anything missed.

**GitHub push fails**
Make sure you're using a Personal Access Token, not your GitHub account password.

**"Posts never loaded" for a course**
That course may have no posts yet, or your session expired. The script skips it and continues with other courses.

**UUID junk files appearing in School Files folder**
These are temp files from interrupted downloads. The script cleans them up automatically at the start of every run.

---

## Contributing

Pull requests are welcome! If you attend a different university with a similar portal system, feel free to adapt this for your school.

1. Fork this repo
2. Create a branch: `git checkout -b my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push: `git push origin my-feature`
5. Open a Pull Request

---

## Disclaimer

This tool is for personal educational use only. Use it responsibly and in accordance with YZU's acceptable use policies. Never share your `.env` file or student credentials with anyone.

---

## License

MIT License — free to use, modify, and share.
