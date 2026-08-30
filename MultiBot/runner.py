import subprocess, sys, os, signal, threading, time

log = os.environ["TEMP"] + "\\multibot_out.txt"
out_lines = []

def reader(stream):
    for line in iter(stream.readline, ""):
        out_lines.append(line)

proc = subprocess.Popen(
    [sys.executable, "-u", "main.py"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    bufsize=0, text=True
)

t = threading.Thread(target=reader, args=(proc.stdout,), daemon=True)
t.start()

time.sleep(40)
try:
    proc.kill()
except:
    pass
proc.wait()
time.sleep(0.5)

with open(log, "w", encoding="utf-8") as f:
    for line in out_lines:
        f.write(line)

with open(log, "r", encoding="utf-8") as f:
    content = f.read()

# Filter for interesting lines
for line in content.split("\n"):
    if any(kw in line for kw in ["[JOIN]", "[WARN]", "[OK]", "[ONLINE]", "Cogs", "AutoJoin", "Node", "Error", "Connected"]):
        print(line)
