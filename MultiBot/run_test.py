import subprocess
import sys
import os
import time
import signal

log_file = os.environ["TEMP"] + "\\multibot_runner_log.txt"
with open(log_file, "w", encoding="utf-8") as f:
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(25)
    # Read available output
    out = ""
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    
    # Also try reading from stdout directly
    import select
    remaining = ""
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        remaining += line
        if "AutoJoin" in line or "[JOIN]" in line or "[OK]" in line or "[WARN]" in line or "ONLINE" in line or "Cogs" in line or "Node" in line or "ERROR" in line:
            f.write(line)
            f.flush()
        if time.time() - start_time > 35:
            break
    
    proc.kill()
    proc.wait()

with open(log_file, "r", encoding="utf-8") as f:
    print(f.read())
