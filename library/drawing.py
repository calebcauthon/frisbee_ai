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
    return annotated_frame