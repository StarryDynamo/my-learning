Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\heave\agents\research-agent"
WshShell.Run "pythonw run_daily_digest.py", 0, False
