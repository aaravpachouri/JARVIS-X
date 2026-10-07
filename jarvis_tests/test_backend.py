import time

from backend.ai_controller import AIController


jarvis = AIController()


def test(command, wait=2):

    print("\n" + "=" * 80)
    print("COMMAND :", command)
    print("=" * 80)

    try:

        jarvis.execute(command)

        print("✅ SUCCESS")

    except Exception as e:

        print("❌ FAILED")
        print(e)

    time.sleep(wait)


##################################################
# APPLICATIONS
##################################################

test("open notepad")

test("open calculator")

##################################################
# WEB
##################################################

test("open youtube")

test("search python programming")

##################################################
# KEYBOARD
##################################################

input("\nClick inside Notepad and press ENTER...")

test("type Hello from JARVIS Mark XI")

##################################################
# MOUSE
##################################################

test("move mouse to 500 500")

test("click")

##################################################
# CLIPBOARD
##################################################

test("copy Hello from JARVIS")

##################################################
# FILE SYSTEM
##################################################

test("create folder Jarvis_Test")

##################################################
# TERMINAL
##################################################

test("run dir")

##################################################
# SCREENSHOT
##################################################

test("take screenshot", wait=4)

##################################################

print("\n")
print("=" * 80)
print("BACKEND TEST COMPLETE")
print("=" * 80)