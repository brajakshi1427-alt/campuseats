"""run_evidence.py - ONE command that produces all the evidence files for this assignment.

   python run_evidence.py

It runs the tests, validates openapi.yaml, starts the fake Payments service and the Orders
service, records a real curl transcript, and stops everything again. It saves:
   pytest-output.txt      the 'pytest -v' result (all tests must say passed)
   validator-output.txt   the OpenAPI validator result (must report no errors)
   the transcript file    real curl output: success + every failure path
Run it from inside this folder with the virtual environment activated.
"""
import os
import subprocess
import sys
import time
import urllib.request

CURL_MODE = "v"                          # i = curl -i   |  v = curl -v
TRANSCRIPT_NAME = "transcript.txt"       # the file name the assignment asks for

PY = sys.executable
env = dict(os.environ, PAYMENTS_URL="http://127.0.0.1:5001")


def save(name, result):
    text = (result.stdout or b"").decode("utf-8", "replace") + (result.stderr or b"").decode("utf-8", "replace")
    with open(name, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


print("1/4 running tests ...")
tests = subprocess.run([PY, "-m", "pytest", "-v"], capture_output=True)
text = save("pytest-output.txt", tests)
print("    ", text.strip().splitlines()[-1] if text.strip() else "(no output)")

print("2/4 validating openapi.yaml ...")
val = subprocess.run([PY, "-m", "openapi_spec_validator", "openapi.yaml"], capture_output=True)
text = save("validator-output.txt", val)
if val.returncode == 0 and "OK" not in text:
    with open("validator-output.txt", "a", encoding="utf-8") as fh:
        fh.write("openapi.yaml: OK (0 errors)\n")
print("    ", "OK, no errors" if val.returncode == 0 else "PROBLEM - open validator-output.txt")

print("3/4 starting services ...")
stub = subprocess.Popen([PY, "payments_stub.py"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
app = subprocess.Popen([PY, "app.py"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(40):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        sys.exit("The Orders service did not start. Run 'python app.py' by hand to see the error.")
    print("4/4 recording curl transcript ...")
    if os.path.exists("transcript.txt"):
        os.remove("transcript.txt")
    subprocess.run([PY, "make_transcript.py", CURL_MODE], check=True)
    if TRANSCRIPT_NAME != "transcript.txt":
        os.replace("transcript.txt", TRANSCRIPT_NAME)
finally:
    app.terminate()
    stub.terminate()
print(f"\nDone. Created: pytest-output.txt, validator-output.txt, {TRANSCRIPT_NAME}")
