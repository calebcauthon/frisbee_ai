import argparse
import os
from tqdm import tqdm
import cv2
import json
from PIL import Image

import supervision as sv

def predict(path):
  command = f"inference infer {path} --api-key pH2eX46dBGLw2Gh1ofek --project-id frisbee-5d4co --model-version 4"
  result = os.popen(command).read().split('\n')
  for line in result:
    if line and not line.startswith("Running"):
      return json.loads(line.replace("'", '"'))

def predict_frame(frame):
  im = Image.fromarray(frame)
  im.save("tmp.jpeg")
  results = predict("tmp.jpeg")
  return results

def initialize_video_processing(source_video_path: str):
  tracker = sv.ByteTrack(track_thresh= 0.25,
      track_buffer = 90,
      match_thresh = 0.6,
      frame_rate = 30,)
  box_annotator = sv.BoxAnnotator()
  label_annotator = sv.LabelAnnotator()
  frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
  video_info = sv.VideoInfo.from_video_path(video_path=source_video_path)

  return tracker, box_annotator, label_annotator, frame_generator, video_info

with open('videos/womens_goalty/ids.json', 'r') as f:
    tracker_names = json.load(f)

def ask_user_for_name(bbox, current_frame_data):
    import random
    random_number = random.randint(0, 10000)
    path = f"videos/womens_goalty/outputs/tracker_ids/tmp{random_number}.jpg"
    try:
        write_bbox_to_file(bbox, current_frame_data["frame"], path)
    except Exception as e:
        print(f"Error writing to file: {e}")
        return "unknown"
    img = cv2.imread(path)
    cv2.imshow('Image', img)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()

    # Ask the user for the name
    name = input("Enter the name: ")

    # Delete the file
    os.remove(path)

    return name

def get_name(tracker_id, bbox, current_frame_data):
  for name, ids in tracker_names.items():
    if tracker_id in ids:
      return name
  else:
     name = ask_user_for_name(bbox, current_frame_data)
     if name in tracker_names:
         tracker_names[name].append(int(tracker_id))
     else:
         tracker_names[name] = [int(tracker_id)]

     # Update the ids.json file
     with open('videos/womens_goalty/ids.json', 'w') as f:
         json.dump(tracker_names, f)


  return f"ID {tracker_id}"

def get_class_name(class_id):
  class_names = {
      0: "bucket",
      1: "one??",
      2: "player",
      3: "frisbee",
      4: "refere"
  }
  return class_names[class_id]

def get_labels(detections, deps):
    labels = [
        f"{get_name(tracker_id, bbox, deps['status']['current_frame'])}"
        for bbox, _, confidence, class_id, tracker_id
        in detections
    ]

    # Blacklist of names
    blacklist_names = ["opp", "ref", "bys"]

    filtered_labels = []
    filtered_xyxy = []
    filtered_class_ids = []
    filtered_tracker_ids = []
    filtered_confidences = []
    for i, label in enumerate(labels):
        clean = True
        for name in blacklist_names: 
            if name == "" or name in label.lower():
                clean = False

        if clean:
            filtered_labels.append(label)
            filtered_xyxy.append(detections.xyxy[i])
            filtered_class_ids.append(detections.class_id[i])
            filtered_tracker_ids.append(detections.tracker_id[i])
            filtered_confidences.append(detections.confidence[i])

    detections.xyxy = filtered_xyxy
    detections.class_id = filtered_class_ids
    detections.tracker_id = filtered_tracker_ids
    detections.confidence = filtered_confidences

    return filtered_labels, detections

def annotate(frame, detections, deps):
  labels, detections = get_labels(detections, deps)
  
  annotated_frame = deps["box_annotator"].annotate(
      scene=frame.copy(), detections=detections, labels=labels
  )

  annotated_labeled_frame = deps["label_annotator"].annotate(
      scene=annotated_frame, detections=detections, labels=labels
  )

  return annotated_labeled_frame

def get_detections(results, deps):
    tracker = deps["tracker"]
    detections = sv.Detections.from_roboflow(results)
    detections = tracker.update_with_detections(detections)

    deps["tracker_data"] = {}
    for bbox, class_id, tracker_id in zip(detections.xyxy, detections.class_id, detections.tracker_id):
        if tracker_id not in deps["tracker_data"]:
            deps["tracker_data"][tracker_id] = {
                "first_frame_data": deps["status"]["frame_data"],
                "first_bbox": bbox,
                "class_id": class_id,
                "name": get_name(tracker_id, bbox, deps["status"]["frame_data"]),
                "bboxes": [bbox],
            }
        else:
            deps["tracker_data"][tracker_id]["bboxes"].append(bbox)

    return detections

def process_video(
    source_video_path: str,
    target_video_path: str,
) -> None:
    tracker, box_annotator, label_annotator, frame_generator, video_info = initialize_video_processing(source_video_path)
    deps = {}
    deps["box_annotator"] = box_annotator
    deps["label_annotator"] = label_annotator
    deps["tracker"] = tracker
    deps["status"] = {}

    with sv.VideoSink(target_path=target_video_path, video_info=video_info) as sink:
        deps["status"]["paths"] = {
            "source_video_path": source_video_path,
            "target_video_path": target_video_path,
            "video_info": video_info
        }
        for index, frame in enumerate(tqdm(frame_generator, total=video_info.total_frames)):
            frame_data = {
              "frame": frame,
              "index": index
            }
            deps["status"]["frame_data"] = frame_data
            deps["status"]["current_frame"] = frame_data

            results = predict_frame(frame)
            detections = get_detections(results, deps)
            annotated_frame = annotate(frame, detections, deps)
            annotated_frame, points = draw_field(annotated_frame)
            left_bucket_top_left = points["left_bucket_top_left"]

            buck_bbox_center = None
            for bbox, class_id in zip(detections.xyxy, detections.class_id):
                class_name = get_class_name(class_id)
                if class_name == "bucket":
                    buck_bbox_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                    break

            if buck_bbox_center is not None:
                for bbox, class_id in zip(detections.xyxy, detections.class_id):
                    if get_class_name(class_id) == "player":
                        player_bbox_bottom_left = (bbox[0], bbox[3])
                        start_point = sv.Point(x=player_bbox_bottom_left[0], y=player_bbox_bottom_left[1])
                        end_point = sv.Point(x=buck_bbox_center[0], y=buck_bbox_center[1])
                        annotated_frame = sv.draw_line(annotated_frame, start_point, end_point, sv.Color.from_hex("#FF0000"))

                        player_delta_from_bucket = {
                           "X": player_bbox_bottom_left[0] - buck_bbox_center[0],
                           "Y": player_bbox_bottom_left[1] - buck_bbox_center[1]
                        }

                        square_width = 10
                        # Calculate the position of the red square based on the player's delta from the bucket
                        # Factor the delta down to fit in the rectangle. Reduce it by 1/10
                        red_square_x = left_bucket_top_left[0] + player_delta_from_bucket["X"] / 10
                        red_square_y = left_bucket_top_left[1] + player_delta_from_bucket["Y"] / 10

                        # Define the top left and bottom right points of the red square
                        red_square_top_left = (red_square_x, red_square_y)
                        red_square_bottom_right = (red_square_top_left[0] + square_width, red_square_top_left[1] + square_width)

                        # Create the red square
                        red_square = sv.Rect(x=red_square_top_left[0], y=red_square_top_left[1], width=red_square_bottom_right[0] - red_square_top_left[0], height=red_square_bottom_right[1] - red_square_top_left[1])

                        # Draw the red square on the annotated frame
                        annotated_frame = sv.draw_filled_rectangle(annotated_frame, red_square, sv.Color.from_hex("#FF0000"))



            sink.write_frame(frame=annotated_frame)


def draw_field(annotated_frame):
    # Draw a white rectangle in the upper left corner of the image
    rectangle_top_left = (0, 0)
    rectangle_top_right = (200, 0)
    rectangle_bottom_left = (0, 200)
    rectangle_bottom_right = (200, 200)

    rectangle = sv.Rect(x=rectangle_top_left[0], y=rectangle_top_left[1], width=rectangle_top_right[0] - rectangle_top_left[0], height=rectangle_bottom_left[1] - rectangle_top_left[1])
    annotated_frame = sv.draw_filled_rectangle(annotated_frame, rectangle, sv.Color.from_hex("#FFFFFF"))

    # Draw two small black squares in the bottom half of the rectangle that are 50px apart
    square_width = 10
    
    rectangle_height = rectangle_bottom_left[1] - rectangle_top_left[1]
    square_y = rectangle_bottom_left[1] - int(rectangle_height * 0.1) - square_width
    middle_x = int((rectangle_bottom_right[0] - rectangle_top_left[0]) / 2)

    square1_top_left = (middle_x - 30, square_y)
    square1_bottom_right = (square1_top_left[0] + square_width, square1_top_left[1] + square_width)
    square1 = sv.Rect(x=square1_top_left[0], y=square1_top_left[1], width=square1_bottom_right[0] - square1_top_left[0], height=square1_bottom_right[1] - square1_top_left[1])

    square2_top_left = (middle_x + 30, square_y)
    square2_bottom_right = (square2_top_left[0] + square_width, square2_top_left[1] + square_width)
    square2 = sv.Rect(x=square2_top_left[0], y=square2_top_left[1], width=square2_bottom_right[0] - square2_top_left[0], height=square2_bottom_right[1] - square2_top_left[1])

    annotated_frame = sv.draw_filled_rectangle(annotated_frame, square1, sv.Color.from_hex("#000000"))
    annotated_frame = sv.draw_filled_rectangle(annotated_frame, square2, sv.Color.from_hex("#000000"))
    return annotated_frame, {
        "left_bucket_top_left": square1_top_left,
    }

def write_bbox_to_file(bbox, frame, filepath):
    bbox = bbox
    x1, y1, x2, y2 = map(int, bbox)
    cropped_frame = frame[y1:y2, x1:x2]
    cv2.imwrite(filepath, cropped_frame)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Video Processing with YOLO and ByteTrack"
    )
    parser.add_argument(
        "--source_video_path",
        required=True,
        help="Path to the source video file",
        type=str,
    )
    parser.add_argument(
        "--target_video_path",
        required=True,
        help="Path to the target video file (output)",
        type=str,
    )

    args = parser.parse_args()

    process_video(
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path
    )