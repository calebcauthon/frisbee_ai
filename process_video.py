import argparse
from tqdm import tqdm
import cv2
from library.detection import predict_frame
from library.drawing import *
from library.homography import *

import supervision as sv

def initialize_video_processing(source_video_path: str):
  box_annotator = sv.BoxAnnotator()
  label_annotator = sv.LabelAnnotator()
  frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
  video_info = sv.VideoInfo.from_video_path(video_path=source_video_path)

  return box_annotator, label_annotator, frame_generator, video_info

def process_video(
    source_video_path: str,
    target_video_path: str,
) -> None:
    box_annotator, label_annotator, frame_generator, video_info = initialize_video_processing(source_video_path)
    _, _l, _f, video_info2 = initialize_video_processing(source_video_path)
    deps = {}
    deps["box_annotator"] = box_annotator
    deps["label_annotator"] = label_annotator
    deps["status"] = {}
    deps["video_info"] = video_info
    deps["source_video_info"] = video_info2
    deps["source_video_path"] = source_video_path
    deps["target_video_path"] = target_video_path
    deps["yardage_points"] = {
      "top_left": (0, 30),
      "top_right": (78, 30),
      "bottom_left": (30, 109),
      "bottom_right": (52, 109)
    }

    print("Processing video...")
    print(f"Video Size: {video_info.width}x{video_info.height}")
    video_info.width += 1200
    # Create a blank image with the new dimensions
    blank_image = np.zeros((video_info.height, video_info.width, 3), np.uint8)

    with sv.VideoSink(target_path=target_video_path, video_info=video_info) as sink:
        deps["sink"] = sink
        for index, frame in enumerate(tqdm(frame_generator, total=video_info.total_frames)):
            if index > 3:
                continue
            # Insert the frame into the blank image
            blank_image[:frame.shape[0], :frame.shape[1]] = frame
            frame_data = {
                "frame": blank_image,
                "index": index
            }
            deps["status"]["frame_data"] = frame_data
            deps["status"]["current_frame"] = frame_data
            process_one_frame(index, blank_image, deps)
            
def process_one_frame(index, frame, deps):
    sink = deps["sink"]

    detections = sv.Detections.from_roboflow(predict_frame(frame, deps))
    frame = annotate(frame, detections, deps)
    frame = draw_field(frame, deps)

    # Draw black rectangles at specified points

    top_left = (422, 153)
    top_right = (1176, 123)
    left_bucket = (693, 581)
    right_bucket = (1181, 567)
    known_points = [top_left, top_right, right_bucket, left_bucket]
    frame = draw_red_rectangle(frame, top_left, deps) # top left
    frame = draw_red_rectangle(frame, top_right, deps) # top right
    frame = draw_red_rectangle(frame, left_bucket, deps) # left bucket
    frame = draw_red_rectangle(frame, right_bucket, deps) # right bucket
    
    # Draw the 4 known points with a yellow rectangle within the green field
    yellow = "#FFFF00"  # Hex code for yellow
    for point in known_points:
        field_point = convert_to_birds_eye(known_points, point)
        frame = draw_rectangle_within_green_field(frame, (field_point[0][0][0], field_point[0][0][1]), yellow, deps)
    
    white = "#FFFFFF"  # Hex code for white
    frame = draw_line(frame, left_bucket, right_bucket, white, deps)
    frame = draw_line_between(frame,deps["yardage_points"]["bottom_left"], deps["yardage_points"]["bottom_right"], white, deps)

    for bbox in detections.xyxy:
        top_left = (int(bbox[0]), int(bbox[1]))
        bottom_right = (int(bbox[2]), int(bbox[3]))

        new_image_point = (int((bbox[0] + bbox[2]) / 2), int(bbox[3]))
        new_field_point = convert_to_birds_eye(known_points, new_image_point)
        frame = draw_black_rectangle_within_green_field(frame, (new_field_point[0][0][0], new_field_point[0][0][1]), deps)

    sink.write_frame(frame=frame)

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