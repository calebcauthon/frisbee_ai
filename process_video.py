import argparse
from tqdm import tqdm
import cv2
from library.detection import predict_frame
from library.drawing import annotate, draw_field

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
    deps = {}
    deps["box_annotator"] = box_annotator
    deps["label_annotator"] = label_annotator
    deps["status"] = {}

    with sv.VideoSink(target_path=target_video_path, video_info=video_info) as sink:
        deps["sink"] = sink
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
          process_one_frame(index, frame, deps)
            
def process_one_frame(index, frame, deps):
    sink = deps["sink"]

    detections = sv.Detections.from_roboflow(predict_frame(frame, deps))
    frame = annotate(frame, detections, deps)
    frame = draw_field(frame, deps)

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