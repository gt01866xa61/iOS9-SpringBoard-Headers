Set sh = CreateObject("WScript.Shell")
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
pyScript = scriptDir & "pdf_watermark.py"

args = ""
For i = 0 To WScript.Arguments.Count - 1
    args = args & " """ & WScript.Arguments(i) & """"
Next

sh.Run "pythonw """ & pyScript & """" & args, 0, False
