import supervision as sv

def get_name(tracker_id, bbox, current_frame_data):
  return f"ID {tracker_id}"

def get_labels(detections, deps):
    labels = [
        f"{get_name(tracker_id, bbox, deps['status']['current_frame'])}"
        for bbox, _, confidence, class_id, tracker_id
        in detections
    ]

    # Blacklist of names
    blacklist_names = ["opp", "ref", "bys", "bucket"]

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
            #filtered_tracker_ids.append(detections.tracker_id[i])
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
    video_height = deps["video_info"].height
    rectangle_width = int(video_height * (78 / 145))
    rectangle_top_left = (deps["video_info"].width - rectangle_width, 0)
    rectangle_bottom_right = (deps["video_info"].width, video_height)

    # Draw the outer rectangle (white border)
    outer_rectangle = sv.Rect(x=rectangle_top_left[0], y=rectangle_top_left[1], width=rectangle_bottom_right[0] - rectangle_top_left[0], height=rectangle_bottom_right[1] - rectangle_top_left[1])
    annotated_frame = sv.draw_filled_rectangle(annotated_frame, outer_rectangle, sv.Color.from_hex("#FFFFFF"))

    # Draw the inner rectangle (green)
    border_width = 5  # Width of the border in pixels
    inner_rectangle_top_left = (rectangle_top_left[0] + border_width, rectangle_top_left[1] + border_width)
    inner_rectangle_bottom_right = (rectangle_bottom_right[0] - border_width, rectangle_bottom_right[1] - border_width)
    inner_rectangle = sv.Rect(x=inner_rectangle_top_left[0], y=inner_rectangle_top_left[1], width=inner_rectangle_bottom_right[0] - inner_rectangle_top_left[0], height=inner_rectangle_bottom_right[1] - inner_rectangle_top_left[1])
    annotated_frame = sv.draw_filled_rectangle(annotated_frame, inner_rectangle, sv.Color.from_hex("#008000"))  # Hex code for green

    return annotated_frame
