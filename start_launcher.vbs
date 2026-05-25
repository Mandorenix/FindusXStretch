Set WshShell = CreateObject("WScript.Shell")
' 0 means hidden window, False means don't wait for it to finish
WshShell.Run "pythonw launcher.py", 0, False
