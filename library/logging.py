import time
import os
import json
from json_tricks import dumps

def write_detection_data_to_file(deps, detections):
    objects = [{
      "objects": detection['objects'],
      "frame_number": detection['frame_number']
    } for detection in detections]
    
    annotation_data = {
      "frames": objects,
      "video_path": deps["target_video_path"],
      "source_path": deps["source_video_path"],
      "source_filename": os.path.basename(deps["source_video_path"]),
    }

    filename = os.path.splitext(os.path.basename(deps["target_video_path"]))[0]
    with open(f'static/annotation_data/{filename}_annotation_data.json', 'w') as f:
        f.write(dumps(annotation_data))

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
