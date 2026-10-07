from automation.clipboard.service import ClipboardService


clipboard = ClipboardService()

clipboard.write("Hello from JARVIS X!")

print(

    clipboard.read()

)

clipboard.clear()

print(

    f"Clipboard after clear: '{clipboard.read()}'"

)