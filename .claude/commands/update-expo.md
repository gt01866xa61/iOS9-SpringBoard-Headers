Display the standard PowerShell update commands for this project. Output exactly this block and nothing else:

```powershell
cd D:\Projects\iOS9-SpringBoard-Headers
Remove-Item MoboRefRN\package-lock.json -Force -ErrorAction SilentlyContinue
git pull origin claude/build-iphone-app-3HKVs
cd MoboRefRN
npm install
npx expo start -c --tunnel
```
