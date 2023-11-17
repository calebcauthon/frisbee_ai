import argparse
from tqdm import tqdm
from library.detection import predict_frame
from library.drawing import *
from library.homography import *
from library import homography
from library.logging import *
import os
import supervision as sv

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

deps = {}

def process_video(
    source_video_path: str,
    target_video_path: str,
) -> None:
    tracker, box_annotator, label_annotator, frame_generator, video_info = initialize_video_processing(source_video_path)
    _t, _, _l, _f, video_info2 = initialize_video_processing(source_video_path)
    global deps
    deps = {}
    deps["logs"] = []
    deps["tracker"] = tracker
    deps["box_annotator"] = box_annotator
    deps["label_annotator"] = label_annotator
    deps["status"] = {}
    deps["video_info"] = video_info
    deps["source_video_info"] = video_info2
    deps["source_video_path"] = source_video_path
    deps["target_video_path"] = target_video_path
    deps["yardage_points"] = homography.get_yardage_points()
    deps["homography_points"] = homography.get_homography_points()

    deps["homography_points"]["calibration"] = {
       "video_known_points": [
          deps["homography_points"]["left_clear_cone"]["position_within_image"],
          deps["homography_points"]["right_clear_cone"]["position_within_image"],
          deps["homography_points"]["left_bucket"]["position_within_image"],
          deps["homography_points"]["right_bucket"]["position_within_image"]
       ],
       "field_known_points": [
          deps["homography_points"]["left_clear_cone"]["position_on_field"],
          deps["homography_points"]["right_clear_cone"]["position_on_field"],
          deps["homography_points"]["left_bucket"]["position_on_field"],
          deps["homography_points"]["right_bucket"]["position_on_field"]
       ]
    }

    clearLogs()
    log(deps, "Processing video...")
    log(deps, f"Video Size: {video_info.width}x{video_info.height}")
    log(deps, f"Output Path: {target_video_path}")
    if os.path.exists(target_video_path):
        log(deps, f"Deleted existing file at {target_video_path}")
        os.remove(target_video_path)
    
    video_info.width += 1200
    blank_image = np.zeros((video_info.height, video_info.width, 3), np.uint8)

    with sv.VideoSink(target_path=target_video_path, video_info=video_info, codec=[*"VP90"]) as sink:
        deps["sink"] = sink
        for index, frame in enumerate(tqdm(frame_generator, total=video_info.total_frames)):
            logReplace(deps, "PROGRESS", "PROGRESS: " + tqdm.format_meter(index, video_info.total_frames, 0, 0))
            
            blank_image[:frame.shape[0], :frame.shape[1]] = frame
            frame_data = {
                "frame": blank_image,
                "index": index
            }
            deps["status"]["frame_data"] = frame_data
            deps["status"]["current_frame"] = frame_data
            process_one_frame(index, blank_image, deps)

    logReplace(deps, "PROGRESS", "PROGRESS: " + tqdm.format_meter(video_info.total_frames, video_info.total_frames, 0, 0))
    log(deps, "COMPLETED")
            
def process_one_frame(index, frame, deps):
    sink = deps["sink"]
    tracker = deps["tracker"]

    detections = sv.Detections.from_roboflow(predict_frame(frame, deps))
    detections = tracker.update_with_detections(detections)

    frame = annotate(frame, detections, deps)
    draw_field(frame, deps)

    draw_video_homography_points(frame, deps)
    draw_projection_homography_points(frame, deps)
    
    draw_video_scoring_line(frame, deps)
    draw_projection_scoring_line(frame, deps)
    
    for bbox, _, confidence, class_id, tracker_id in detections:
      draw_player_projection(bbox, frame, deps)

    sink.write_frame(frame=frame)

def draw_player_projection(bbox, frame, deps):
  new_image_point = (int((bbox[0] + bbox[2]) / 2), int(bbox[3]))
  new_field_point = convert_to_birds_eye(new_image_point, deps)
  frame = draw_black_rectangle_within_green_field(frame, (new_field_point[0][0][0], new_field_point[0][0][1]), deps)
  return frame


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