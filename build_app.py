import os, platform, subprocess, sys

def build():
    os_name = platform.system().lower()
    sep = os.pathsep
    cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--name", f"NeatFlow-{os_name}", "--add-data", f"config.yaml{sep}.", "src/neatflow/cli.py"]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    build()
