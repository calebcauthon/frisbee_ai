import time
import os

def clearLogs():
    with open('output.txt', 'w') as f:
        f.write(f"File created at: {time.ctime(os.path.getctime('output.txt'))}\n")

def log(deps, message):
    deps["logs"].append(message)
    print(f"LOG: {message}")
    append_to_output_file(message)

def logReplace(deps, starting_word, new_message):
    for i, entry in enumerate(deps["logs"]):
        if entry.startswith(starting_word):
            deps["logs"][i] = new_message
            rewriteLogs(deps["logs"])
            break
    else:  # This else clause will execute if the for loop completes without a break
        log(deps, new_message)

def rewriteLogs(logs):
    clearLogs()
    for log in logs:
        append_to_output_file(log)

def append_to_output_file(message):
    if not os.path.exists('output.txt'):
        with open('output.txt', 'w') as f:
            pass
    with open('output.txt', 'a') as f:
        f.write(message + '\n')
