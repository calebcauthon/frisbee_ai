import time
import os
import json
from json_tricks import dumps, loads
from library import tracker

def get_annotation_data(filename):
    annotation_file = os.path.join('web_ui', 'static', 'annotation_data', filename)
    print(f"\033[94mReading annotation file {annotation_file}\033[0m")
    if not os.path.exists(annotation_file):
        print(f"Annotation file {annotation_file} does not exist")
        return {}
    with open(annotation_file, 'r') as f:
        obj = loads(f.read())

    return obj

def add_tracker_name(new_name, video_path):
    annotation_data = read_detection_data_from_file(video_path)
    tracker.add_tracker_name(new_name, annotation_data["tracker_names"]) 
    write_annotation_data_to_file(video_path, annotation_data)

def update_tracker_names_based_on_tracker_map(frames, tracker_map):
    for frame in frames:
        for obj in frame["objects"]:
          for name, ids in tracker_map.items():
              if obj["tracker_id"] in ids:
                  obj["tracker_name"] = name
                  break

def move_tracking_id_to_another_name(old_tracker_id, new_name, video_path):
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    annotation_filename = f"{video_filename}_annotation_data.json"
    annotation_data = get_annotation_data(annotation_filename)
    tracker.move_tracking_id_to_another_name(old_tracker_id, new_name, annotation_data["tracker_names"])
    update_tracker_names_based_on_tracker_map(annotation_data["frames"], annotation_data["tracker_names"])
    write_annotation_data_to_file(video_path, annotation_data)

def change_tracker_name(old_name, new_name, video_path):
    annotation_data = read_detection_data_from_file(video_path)
    tracker.change_name(old_name, new_name, annotation_data["tracker_names"])
    update_tracker_names_based_on_tracker_map(annotation_data["frames"], annotation_data["tracker_names"])
    write_annotation_data_to_file(video_path, annotation_data)

def write_detection_data_to_file(deps, detections):
    frames = [{
      "objects": detection['objects'],
      "frame_number": detection['frame_number']
    } for detection in detections]
    
    annotation_data = {
      "frames": frames,
      "video_path": deps["target_video_path"],
      "source_path": deps["source_video_path"],
      "source_filename": os.path.basename(deps["source_video_path"]),
      "tracker_names": deps["tracker_names"]
    }

    write_annotation_data_to_file(deps["target_video_path"], annotation_data)

def write_annotation_data_to_file(video_path, annotation_data):
    filename = os.path.splitext(os.path.basename(video_path))[0]
    with open(f'web_ui/static/annotation_data/{filename}_annotation_data.json', 'w') as f:
        f.write(dumps(annotation_data))

def read_detection_data_from_file(path):
    print(f"Obsolte function read_detection_data_from_file() called with path {path}")
    exit()
    filename = os.path.splitext(os.path.basename(path))[0]
    annotation_file = os.path.join('web_ui', 'static', 'annotation_data', f'{filename}_annotation_data.json')
    print(f"\033[94mReading annotation file {annotation_file}\033[0m")
    if not os.path.exists(annotation_file):
        return {
            "tracker_names": {},
        }
    with open(annotation_file, 'r') as f:
        annotation_data = json.loads(f.read())

    return annotation_data

def clearLogs():
    with open('web_ui/output.txt', 'w') as f:
        f.write(f"File created at: {time.ctime(os.path.getctime('web_ui/output.txt'))}\n")

def log(deps, message):
    #deps["logs"].append(message)
    print(f"LOG: {message}")
    #append_to_output_file(message)

def logReplace(deps, starting_word, new_message):
    return
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
    if not os.path.exists('web_ui/output.txt'):
        with open('web_ui/output.txt', 'w') as f:
            pass
    with open('web_ui/output.txt', 'a') as f:
        f.write(message + '\n')

def split_tracker_id(tracker_id, frame_number, video_path):
    video_file_without_extension = os.path.splitext(os.path.basename(video_path))[0]
    annotation_filename = f"{video_file_without_extension}_annotation_data.json"
    annotation_data = get_annotation_data(annotation_filename)
    tracker.split_tracker_id(tracker_id, frame_number, annotation_data["tracker_names"], annotation_data["frames"])
    update_tracker_names_based_on_tracker_map(annotation_data["frames"], annotation_data["tracker_names"])
    write_annotation_data_to_file(video_path, annotation_data)

def remove_player(name, video_path):
    annotation_data = read_detection_data_from_file(video_path)
    tracker.remove_tracker_name(name, annotation_data["tracker_names"], annotation_data["frames"])
    update_tracker_names_based_on_tracker_map(annotation_data["frames"], annotation_data["tracker_names"])
    write_annotation_data_to_file(video_path, annotation_data)
