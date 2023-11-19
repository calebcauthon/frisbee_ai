import pprint
import cv2

pp = pprint.PrettyPrinter(indent=4)

def gif_route(module_dependencies, filename, player):
    os = module_dependencies.os
    subprocess = module_dependencies.subprocess
    flask = module_dependencies.flask
    drawing = module_dependencies.drawing
    logging = module_dependencies.logging
    stats = module_dependencies.stats

    annotation_filename = f'{filename}_annotation_data.json'
    annotation_data = logging.get_annotation_data(annotation_filename)
    player_frames = stats.get_player_frames(player, annotation_data)
    images = []

    path = f"web_ui/static/video_targets/{filename}.mp4"
    print(f"Opening {path}")
    video = cv2.VideoCapture(path)
    if not video.isOpened():
        print("\033[91mError opening video stream or file\033[0m")
        exit()
    else:
        print("\033[92mOpened video stream or file\033[0m")
    
    
    for index, frame in enumerate(player_frames):
        for obj in frame['objects']:
            if obj['tracker_name'] == player:
                video.set(cv2.CAP_PROP_POS_FRAMES, frame['frame_number'])
                ret, cv2_frame = video.read()
                cropped_image = cv2_frame[int(obj['xyxy'][1])-10:int(obj['xyxy'][3])+10, int(obj['xyxy'][0])-10:int(obj['xyxy'][2])+10]
                cropped_image_path = f'tmp/cv2_{player}_frame_{index}.jpg'
                cv2.imwrite(cropped_image_path, cropped_image)
                images.append(cropped_image_path)
                break # out of objects
                
    output = f"tmp/output_{player}.gif"
    command = ['ffmpeg', '-y', '-i', f"tmp/cv2_{player}_frame_%d.jpg", '-vf', 'setpts=2.0*PTS', '-y', output]
    print("\033[92mRunning {' '.join(command)}\033[0m")
    subprocess.call(command)
    gif_output = flask.send_file(output, mimetype='image/gif')

    for image in images:
        os.remove(image)
    os.remove(output)

    return gif_output

def test_debug():
    import subprocess
    import os

    deps = mock.Mock()
    deps.os = os#mock.Mock()
    deps.subprocess = subprocess#mock.Mock()
    deps.flask = mock.Mock()
    deps.drawing = mock.Mock()
    deps.logging = logging
    deps.stats = mock.Mock()
    def mock_get_player_frames(*args, **kwargs):
        player_frames = stats.get_player_frames(*args, **kwargs)
        return player_frames
    deps.stats.get_player_frames = mock_get_player_frames
    gif_route(deps, "womens_goalty_10_annotated", "JJ")

    print("\033[92mtest_debug passed \033[0m")

if __name__ == "__main__":
    import sys
    import mock
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + '/../../')
    from library import logging, stats, drawing

    if len(sys.argv) > 1 and sys.argv[1] == "test":
      test_debug()
