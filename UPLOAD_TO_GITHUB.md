# Upload to GitHub

If automated upload is blocked by missing or expired GitHub authentication, run:

```bash
cd "D:\Codex 自动化\eeg-github-projects\eeg-bids-sidecar-auditor"
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
$env:ALL_PROXY="http://127.0.0.1:7897"
$env:http_proxy="http://127.0.0.1:7897"
$env:https_proxy="http://127.0.0.1:7897"
$env:all_proxy="http://127.0.0.1:7897"
& "D:\Tools\GitHub CLI\gh.exe" auth login
& "D:\Tools\GitHub CLI\gh.exe" repo create 2241314647/eeg-bids-sidecar-auditor --public --source . --remote origin --push
```

If the repository already exists:

```bash
git remote add origin https://github.com/2241314647/eeg-bids-sidecar-auditor.git
git push -u origin main
```
