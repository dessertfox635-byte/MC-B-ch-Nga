# Xưởng Phim – cài trên Windows 10/11 (PowerShell, chạy với quyền thường).
#   powershell -ExecutionPolicy Bypass -File setup\install_windows.ps1
$ErrorActionPreference = "Stop"
$Dest = if ($env:XUONG_DIR) { $env:XUONG_DIR } else { Join-Path $HOME "Documents\Xuong Phim" }
function Step($m) { Write-Host "`n> $m" -ForegroundColor Green }

Step "1/6 ffmpeg, Node, Python 3.12, Git (winget)"
winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Python.Python.3.12
winget install -e --id Git.Git
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")

Step "2/6 Claude Code"
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { irm https://claude.ai/install.ps1 | iex }

Step "3/6 Mã nguồn → $Dest"
$Here = Split-Path -Parent $PSScriptRoot
if (Test-Path (Join-Path $Here "xuong\__main__.py")) { $Dest = $Here }
elseif (Test-Path (Join-Path $Dest ".git")) { git -C $Dest pull --ff-only }
else { git clone https://github.com/dessertfox635-byte/MC-B-ch-Nga.git $Dest }
Set-Location $Dest

Step "4/6 Python .venv + thư viện"
if (-not (Test-Path ".venv")) { py -3.12 -m venv .venv }
.\.venv\Scripts\python -m pip install -q --upgrade pip
.\.venv\Scripts\pip install -q -r requirements.txt

Step "5/6 GSAP + Chromium"
npm install --silent
npx --yes playwright install chromium

Step "6/6 Kiểm tra"
.\.venv\Scripts\python -m xuong doctor
Write-Host "`nDùng Git Bash để chạy: ./dung-phim.sh inbox/video.mp4 `"yêu cầu`""
