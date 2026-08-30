$env:PYTHONIOENCODING='utf-8'
$logFile = "$env:TEMP\multibot_log.txt"
$proc = Start-Process -FilePath "py" -ArgumentList "-3.13 main.py" -NoNewWindow -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru
Start-Sleep -Seconds 35
$proc.Kill()
Get-Content $logFile | Select-String -Pattern "\[JOIN\]|\[OK\]|\[WARN\]|AutoJoin|Cogs|ONLINE|Error|Connected|Node"
