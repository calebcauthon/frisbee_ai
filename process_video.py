import argparse
from tqdm import tqdm
from library.detection import predict_frame
from library.drawing import *
from library.homography import *
from library import homography
from library.logging import *
from library import logging
from library import stats
import os
import supervision as sv
import pprint
pp = pprint.PrettyPrinter(indent=4)


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
    frame_limit: int = None,
    use_predictions_from_annotations_file: str = None
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
    deps["homography_points"]["calibration"] = homography.get_calibration_points(deps)
    deps["params"] = {
       "frame_limit": frame_limit,
       "use_predictions_from_annotations_file": use_predictions_from_annotations_file
    }

    clearLogs()
    log(deps, "Redrawing video...")
    log(deps, f"Video Size: {video_info.width}x{video_info.height}")
    log(deps, f"Output Path: {target_video_path}")
    if (frame_limit is not None):
        log(deps, f"Frame Limit: {frame_limit}")
    if os.path.exists(target_video_path):
        log(deps, f"Deleted existing file at {target_video_path}")
        os.remove(target_video_path)
    
    video_info.width += 1200
    blank_image = np.zeros((video_info.height, video_info.width, 3), np.uint8)

    print("\033[33m" + f"Loaded video {source_video_path} with {video_info.total_frames} frames" + "\033[0m")
    
    deps["tracker_names"] = {}
    with sv.VideoSink(target_path=target_video_path, video_info=video_info, codec=[*"mp4v"]) as sink:
        deps["sink"] = sink
        for index, frame in enumerate(tqdm(frame_generator, total=video_info.total_frames)):
            if (frame_limit is not None and index >= frame_limit):
                print("\033[33m" + f"Stopping after {frame_limit} frames" + "\033[0m")
                break
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
    logging.write_detection_data_to_file(deps, deps["detections"])
    log(deps, "Wrote detection data to file")
    log(deps, "COMPLETED")
    
def save_detections(frame, frame_number, detections, projections, inference, deps):
    if "detections" not in deps:
        deps["detections"] = []

    objects = []
    for index, entry in enumerate(detections.xyxy):
        prediction = inference["predictions"][index]
        objects.append({
            "field_position": projections[index],
            "confidence": detections.confidence[index],
            "class_id": detections.class_id[index],
            "tracker_id": detections.tracker_id[index],
            "tracker_name": get_name(deps, detections.tracker_id[index]),
            "xyxy": detections.xyxy[index].tolist(),
            "class": prediction["class"],
            "width": int(prediction["width"]),
            "height": int(prediction["height"]),
        })


    detection_map = {
        "frame": frame,
        "frame_number": frame_number,
        "detections": detections,
        "objects": objects
    }
    deps["detections"].append(detection_map)
            
def process_one_frame(index, frame, deps):
    sink = deps["sink"]
    tracker = deps["tracker"]

    detections = None
    if (deps["params"]["use_predictions_from_annotations_file"] is None):
        roboflow_result = predict_frame(frame, deps)
        detections = sv.Detections.from_roboflow(roboflow_result)
        detections = tracker.update_with_detections(detections)
    else:
        if "existing_annotation_data" not in deps:
            annotation_full_path = deps["params"]["use_predictions_from_annotations_file"]
            annotation_filename_only = os.path.basename(annotation_full_path)
            deps["existing_annotation_data"] = logging.get_annotation_data(annotation_filename_only)
            print("\033[92m" + f"Loaded {len(deps['existing_annotation_data']['frames'])} frames from {annotation_filename_only} existing annotation data" + "\033[0m")

            video_info = deps["video_info"]
            existing_annotation_data = deps["existing_annotation_data"]
            if (len(existing_annotation_data['frames']) != video_info.total_frames):
                print("\033[91m" + f"Frame Mismatch Error: frames in annotation data ({len(existing_annotation_data['frames'])}) != frames in video ({video_info.total_frames})" + "\033[0m")
                exit()
            else:
                print("\033[92m" + f"Frame Match: frames in annotation data ({len(existing_annotation_data['frames'])}) == frames in video ({video_info.total_frames})" + "\033[0m")

            tracker_names = existing_annotation_data["tracker_names"].keys()
            for name in tracker_names:
                stats.get_distance_travelled(name, existing_annotation_data['frames'])

        existing_annotation_data = deps["existing_annotation_data"]

        deps["tracker_names"] = existing_annotation_data["tracker_names"]
        existing = existing_annotation_data["frames"][index]["objects"]
        existing_in_roboflow_format = []
        for obj in existing:
            existing_in_roboflow_format.append({
                "x": (obj["xyxy"][0] + obj["xyxy"][2]) / 2.0,
                "y": (obj["xyxy"][1] + obj["xyxy"][3]) / 2.0,
                "width": obj["xyxy"][2] - obj["xyxy"][0],
                "height": obj["xyxy"][3] - obj["xyxy"][1],
                "confidence": obj["confidence"],
                "class": obj["class"],
                "class_id": obj["class_id"],
                "tracker_id": obj["tracker_id"]
            })
        roboflow_result = {
            "image": {
                "width": frame.shape[1],
                "height": frame.shape[0]
            }
        }
        roboflow_result["predictions"] = existing_in_roboflow_format
        detections = sv.Detections.from_roboflow(roboflow_result)
    

    frame = annotate(frame, detections, deps)
    draw_field(frame, deps)

    draw_video_homography_points(frame, deps)
    draw_projection_homography_points(frame, deps)
    
    draw_video_scoring_line(frame, deps)
    draw_projection_scoring_line(frame, deps)
    
    projections = []
    for bbox, _, confidence, class_id, tracker_id in detections:
      projection = get_player_projection(bbox, deps)
      draw_player_projection(projection, frame, deps)
      projections.append(projection)

    save_detections(frame, index, detections, projections, roboflow_result, deps)
    sink.write_frame(frame=frame)


def get_player_projection(bbox, deps):
    new_image_point = (int((bbox[0] + bbox[2]) / 2), int(bbox[3]))
    new_field_point = convert_to_birds_eye(new_image_point, deps)
    xy = (new_field_point[0][0][0], new_field_point[0][0][1])
    return xy

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
    parser.add_argument(
        "--frame_limit",
        required=False,
        help="Limit the number of frames to process",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--use_predictions_from_annotations_file",
        required=False,
        help="Path to the annotation file",
        type=str,
        default=None,
    )

    

    args = parser.parse_args()

    process_video(
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path,
        frame_limit=args.frame_limit,
        use_predictions_from_annotations_file=args.use_predictions_from_annotations_file
    )