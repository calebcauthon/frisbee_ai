def annotate_video_route(dependencies):
    source_video_path = get_source_video_path(dependencies)
    frame_limit_flag = get_frame_limit(dependencies)
    annotation_filename_flag = get_annotation_filename(dependencies)

    source_filename = dependencies.os.path.basename(source_video_path)
    source_filename = dependencies.os.path.splitext(source_filename)[0]

    target_video_path = f'web_ui/static/video_targets/{source_filename}_annotated.mp4'
    command = f"poetry shell && python process_video.py --source_video_path web_ui/static/{source_video_path} --target_video_path {target_video_path} {frame_limit_flag} {annotation_filename_flag}"
    print(f"\033[33mRunning {command}\033[0m")
    dependencies.subprocess.Popen(command, shell=True)
    return {"message": "Video processing started"}, 200

def get_annotation_filename(dependencies):
    flask = dependencies.flask
    data = flask.request.get_json()
    annotation_filename = data.get('annotation_file')
    if annotation_filename is None:
        return ""
    else:
      return f"--use_predictions_from_annotations_file web_ui/static/annotation_data/{annotation_filename}"

def get_source_video_path(dependencies):
    flask = dependencies.flask
    data = flask.request.get_json()
    source_video_path = data.get('source_video_path')
    source_video_path = source_video_path.split('static', 1)[-1]
    if source_video_path.startswith('//'):
        source_video_path = source_video_path[1:]

    return source_video_path

def get_frame_limit(dependencies):
    data = dependencies.flask.request.get_json()
    frame_limit = data.get('frame_limit')
    if frame_limit is not None:
        frame_limit_flag = f"--frame_limit {frame_limit}"
    else:
        frame_limit_flag = ""

    return frame_limit_flag