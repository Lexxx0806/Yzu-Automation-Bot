📚 YZU Portal File Downloader
An automated tool that logs into the YZU (Yuan Ze University) Portal and downloads all course files (PDFs, PowerPoints, Word docs, etc.) across all your courses — organized into folders on your laptop and optionally pushed to GitHub.

Built by a YZU student, for YZU students. Contributions welcome!

✨ Features
🔐 Auto-login to the YZU portal
🌐 Switches portal to English automatically
📂 Downloads files from all your courses at once
🗂️ Organizes files into folders by course name
⏭️ Skips files you've already downloaded
🐙 Auto-pushes new files to a GitHub repo (optional)
🗑️ Cleans up junk temp files automatically
🖥️ Requirements
Windows 10/11
Python 3.10+ — ⚠️ check "Add Python to PATH" during install
Git (only needed for GitHub push feature)
🚀 Setup (First Time Only)
Step 1 — Clone or download this repo
git clone https://github.com/YourUsername/Yzu-Automation-Bot.git
cd Yzu-Automation-Bot
Or click the green Code button → Download ZIP and extract it.

Step 2 — Install dependencies
Open a terminal in the project folder and run:

pip install playwright python-dotenv
python -m playwright install chromium
Step 3 — Create your .env file
Create a file called .env in the project folder (same folder as downloader.py):

YZU_USERNAME=your_student_id
YZU_PASSWORD=your_password
⚠️ Never share this file or commit it to GitHub. It's already listed in .gitignore so it won't be uploaded automatically.

Step 4 — Edit config.json
Open config.json and update:

{
    "portal_url": "https://portalx.yzu.edu.tw/PortalSocialVB/Login.aspx",
    "download_folder": "C:/Users/YourName/Desktop/School Files",
    "github_enabled": false,
    "github_repo_url": "",
    "github_branch": "main"
}
Set download_folder to wherever you want files saved on your laptop
Replace YourName with your actual Windows username
Step 5 — Add your courses
Open downloader.py and find the YZU_COURSES dictionary near the top. Replace the PageIDs with your own courses:

YZU_COURSES = {
    "32440": "Introduction to Algorithms",
    "31221": "Introduction to Operating System",
    "26811": "Information Privacy",
    "28726": "Assembly Language and Computer Organization",
    "26807": "Probability and Statistics",
    "32213": "Machine Learning",
}
How to find your PageID:

Log into the portal
Click on a course from the left sidebar
Look at the URL — it will contain PageID=XXXXX
Copy that number into the dictionary above
▶️ Running the Downloader
Open a terminal in the project folder and run:

python downloader.py
The script will:

Open a browser and log in automatically
Switch the portal to English
Go through each course and download all files
Organize everything into folders
Push to GitHub (if enabled)
🐙 GitHub Auto-Push (Optional)
If you want files automatically pushed to a GitHub repo after each download:

Create a new private repository on GitHub (e.g. yzu-course-files)
In config.json, set:
"github_enabled": true,
"github_repo_url": "https://github.com/YourUsername/yzu-course-files.git",
"github_branch": "main"
In your terminal, connect the download folder to GitHub:
cd "C:/Users/YourName/Desktop/School Files"
git init -b main
git remote add origin https://github.com/YourUsername/yzu-course-files.git
git add .
git commit -m "Initial commit"
git push -u origin main
After that, every time you run downloader.py, new files will be committed and pushed automatically.

📁 Folder Structure
After running, your files will be organized like this:

School Files/
├── Introduction to Algorithms/
│   ├── asymptotic analysis-1.pptx
│   └── Lecture 1 - Introduction to Algorithms.pdf
├── Machine Learning/
│   ├── linear perceptron links.pptx
│   └── 04 linear classification perceptron.pdf
├── Information Privacy/
│   └── 20260316 Social Networks.pdf
└── ...
🔧 Troubleshooting
"No module named playwright" → Run pip install playwright then python -m playwright install chromium

Login fails → Make sure your .env file has the correct student ID and password. Try logging in manually on the portal to verify.

Files not found for a course → The script waits up to 30 seconds for the portal to load posts. If your internet is slow, the portal may time out. Try running again.

GitHub push fails → Make sure you've set up the git remote in your download folder (see GitHub section above).

"Posts never loaded" for a course → That course may have no posts yet, or your session expired. The script will skip it and continue with other courses.

🤝 Contributing
Pull requests are welcome! If you go to a different university with a similar portal system, feel free to adapt this for your school.

Fork this repo
Create a branch: git checkout -b my-feature
Commit your changes: git commit -m "Add my feature"
Push: git push origin my-feature
Open a Pull Request
⚠️ Disclaimer
This tool is for personal educational use only. Use it responsibly and in accordance with YZU's acceptable use policies. Never share your .env file or student credentials with anyone.

📄 License
MIT License — free to use, modify, and share.
