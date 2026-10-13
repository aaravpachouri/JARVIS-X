# JARVIS-X Windows Integration Checklist

Use this checklist after reviewing the consolidated audit branch. CI runs on Linux with mocked/unit-level checks; it does not prove that the real desktop, Ollama vision model, microphone, or Qt lifecycle works on Windows.

## 1. Check out the audit branch

```powershell
git fetch origin
git switch audit/jarvis-x-stability-2026-10
git pull
```

## 2. Run automated tests locally

Activate the project's existing virtual environment, then run:

```powershell
python -m pytest -q
python -m compileall -q ai automation backend business_outreach core ui voice
```

Record the full test output, Python version, and any failing test names.

## 3. Verify the local Ollama model

```powershell
ollama list
ollama run qwen3-vl:4b-instruct "Reply with only OK"
```

The text-only response confirms text inference only. It does not confirm that the model accepts and interprets screenshots. Confirm that the model tag shown by JARVIS matches the model actually configured. To use another installed model, set `JARVIS_LOCAL_MODEL` before launching JARVIS.

## 4. Test vision independently of the app\n\nRun the isolated smoke test from the repository root with the same activated environment used to launch JARVIS:\n\n```powershell\npython scripts/diagnose_ollama_vision.py\n```\n\nIt captures one screenshot, sends a read-only description request to the configured local model, reports elapsed time, and deletes its temporary screenshot. It does not start the voice listener or execute desktop actions. If you prefer, test an existing image with `python scripts/diagnose_ollama_vision.py --image path\\to\\image.png`.\n\n## 5. Reproduce the computer-agent task with diagnostics visible

Launch JARVIS from the same terminal so logs remain visible. Ask it to open YouTube. Record:
- Whether `OBSERVE: Capturing screenshot` appears.
- Whether `OBSERVE: Screenshot ready` appears.
- Whether `THINK: Sending screenshot and prompt` appears.
- Whether `THINK: Model response received` appears, including elapsed seconds.
- The final action and whether the browser visibly reaches YouTube.

If it stalls, copy the logs from `STEP 1` through the last emitted line. Do not interpret a text-only Ollama response as a successful vision test.

## 6. Verify cancellation and UI responsiveness

- Start a computer task and use the existing stop/interrupt control while the model is thinking.
- Confirm that the UI still responds and that a late model result does not trigger a new action after cancellation.
- Start and stop voice listening; confirm the UI responds and no duplicate listener starts.
- Close JARVIS after a task has completed and check for Qt warnings about a thread still running.

## 7. Verify safety gates

- Confirm the computer agent rejects `RUN_COMMAND`, `RUN_PYTHON`, destructive filesystem actions, and shutdown/restart/sleep where no explicit confirmation workflow exists.
- Confirm WhatsApp outreach is blocked for an unapproved lead.
- In the command-line outreach workflow, confirm the explicit `y` decision permits opening the prepared chat and `n` does not.
- Confirm website-search failures or unmatched results remain UNKNOWN and are not automatically treated as proof that a business has no website.

## 8. Report results

For each item, mark PASS, FAIL, or NOT TESTED and include the relevant log excerpt. Do not mark the application fully verified until the real Windows/Ollama/voice checks have passed.
