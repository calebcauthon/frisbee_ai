import supervision as sv
import numpy as np
from library.homography import *
from library import logging
import json
import random

def get_tracker_data(deps):
    if "tracker_names" not in deps:
        data = logging.read_detection_data_from_file(deps["target_video_path"])
        deps["tracker_names"] = data["tracker_names"]
    return deps["tracker_names"]


def draw_player_projection(projection, frame, deps):
    frame = draw_black_rectangle_within_green_field(frame, (projection[0], projection[1]), deps)
    return frame

def invent_name():
    girls_names = ["Emma", "Olivia", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia", "Harper", "Evelyn"]
    return random.choice(girls_names)

def get_name(deps, tracker_id):
  tracker_names = get_tracker_data(deps)
  for name, ids in tracker_names.items():
    if tracker_id in ids:
      return name
  else:
     name = invent_name()
     if name in tracker_names:
         tracker_names[name].append(int(tracker_id))
     else:
         tracker_names[name] = [int(tracker_id)]

def get_labels(detections, deps):
    labels = [
        f"{get_name(deps, tracker_id)}"
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

def draw_field(annotated_frame, deps):
    # Draw a rectangle on the right side of the video with a height-to-width ratio of 145 to 78
    video_height = deps["source_video_info"].height
    rectangle_width = 600
    rectangle_top_left = (deps["source_video_info"].width, 0)
    rectangle_bottom_right = (deps["source_video_info"].width + rectangle_width, video_height)
    rectangle_height = rectangle_bottom_right[1] - rectangle_top_left[1]

    deps["green_field_coordinates"] = {
        "top_left": rectangle_top_left,
        "bottom_right": rectangle_bottom_right,
        "width": rectangle_width,
        "height": rectangle_height
    }

    # Draw the outer rectangle (white border)
    outer_rectangle = sv.Rect(x=rectangle_top_left[0], y=rectangle_top_left[1], width=rectangle_bottom_right[0] - rectangle_top_left[0], height=rectangle_bottom_right[1] - rectangle_top_left[1])
    sv.draw_filled_rectangle(annotated_frame, outer_rectangle, sv.Color.from_hex("#FFFFFF"))

    # Draw the inner rectangle (green)
    border_width = 5  # Width of the border in pixels
    inner_rectangle_top_left = (rectangle_top_left[0] + border_width, rectangle_top_left[1] + border_width)
    inner_rectangle_bottom_right = (rectangle_bottom_right[0] - border_width, rectangle_bottom_right[1] - border_width)
    inner_rectangle = sv.Rect(x=inner_rectangle_top_left[0], y=inner_rectangle_top_left[1], width=inner_rectangle_bottom_right[0] - inner_rectangle_top_left[0], height=inner_rectangle_bottom_right[1] - inner_rectangle_top_left[1])
    sv.draw_filled_rectangle(annotated_frame, inner_rectangle, sv.Color.from_hex("#008000"))  # Hex code for green

def convert_from_yardage_position_on_field_to_pixel_position_on_green_rectangle(position, deps):
    # Scale the position to fit the green field dimensions
    green_field_width = deps["green_field_coordinates"]["width"]
    green_field_height = deps["green_field_coordinates"]["height"]
    field_width_in_feet = 78
    field_height_in_feet = 145

    # Calculate the scaled position
    scaled_position = (
        int(position[0] * green_field_width / field_width_in_feet),
        int(position[1] * green_field_height / field_height_in_feet)
    )

    # Offset the position to be within the green rectangle
    offset_position = (
        scaled_position[0] + deps["green_field_coordinates"]["top_left"][0],
        scaled_position[1] + deps["green_field_coordinates"]["top_left"][1]
    )

    return offset_position

def draw_line_between(frame, yardage_point_1, yardage_point_2, color, deps):
    pixel_position_1 = convert_from_yardage_position_on_field_to_pixel_position_on_green_rectangle(yardage_point_1, deps)
    pixel_position_2 = convert_from_yardage_position_on_field_to_pixel_position_on_green_rectangle(yardage_point_2, deps)

    draw_line(frame, pixel_position_1, pixel_position_2, color, deps)

def draw_line(frame, pixel_position_1, pixel_position_2, color, deps):
    start_point = sv.Point(x=pixel_position_1[0], y=pixel_position_1[1])
    end_point = sv.Point(x=pixel_position_2[0], y=pixel_position_2[1])
    sv.draw_line(frame, start_point, end_point, sv.Color.from_hex(color), thickness=2)

def draw_rectangle_within_green_field(frame, yardage_position, color, deps):
    pixel_position = convert_from_yardage_position_on_field_to_pixel_position_on_green_rectangle(yardage_position, deps)
    draw_rectangle(frame, pixel_position, color, deps)

def draw_black_rectangle_within_green_field(frame, yardage_position, deps):
    black = "#000000"
    draw_rectangle_within_green_field(frame, yardage_position, black, deps)

def draw_rectangle(frame, position, color, deps):
    width = 10
    height = 10
    rectangle = sv.Rect(x=position[0], y=position[1], width=width, height=10)  # Arbitrary width and height
    sv.draw_filled_rectangle(frame, rectangle, sv.Color.from_hex(color))  # Hex code for color

def draw_black_rectangle(frame, position, deps):
    draw_rectangle(frame, position, "#000000", deps)

def draw_red_rectangle(frame, position, deps):
    draw_rectangle(frame, position, "#FF0000", deps)

def draw_video_homography_points(frame, deps):
    top_left = deps["homography_points"]["left_clear_cone"]["position_within_image"]
    top_right = deps["homography_points"]["right_clear_cone"]["position_within_image"]
    left_bucket = deps["homography_points"]["left_bucket"]["position_within_image"]
    right_bucket = deps["homography_points"]["right_bucket"]["position_within_image"]
    
    draw_red_rectangle(frame, top_left, deps) # top left
    draw_red_rectangle(frame, top_right, deps) # top right
    draw_red_rectangle(frame, left_bucket, deps) # left bucket
    draw_red_rectangle(frame, right_bucket, deps) # right bucket
  
def draw_video_scoring_line(frame, deps):
  left_bucket = deps["homography_points"]["left_bucket"]["position_within_image"]
  right_bucket = deps["homography_points"]["right_bucket"]["position_within_image"]
  white = "#FFFFFF"  # Hex code for white
  draw_line(frame, left_bucket, right_bucket, white, deps)

def draw_projection_scoring_line(frame, deps):
  left_bucket = deps["homography_points"]["left_bucket"]["position_on_field"]
  right_bucket = deps["homography_points"]["right_bucket"]["position_on_field"]
  white = "#FFFFFF"  # Hex code for white
  draw_line_between(frame, left_bucket, right_bucket, white, deps)

def draw_projection_homography_points(frame, deps):
  known_points = deps["homography_points"]["calibration"]["video_known_points"]
  # Draw the 4 known points with a yellow rectangle within the green field
  yellow = "#FFFF00"  # Hex code for yellow
  for point in known_points:
      field_point = convert_to_birds_eye(point, deps)
      draw_rectangle_within_green_field(frame, (field_point[0][0][0], field_point[0][0][1]), yellow, deps)
