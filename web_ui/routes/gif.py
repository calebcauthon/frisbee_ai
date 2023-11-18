import pprint
pp = pprint.PrettyPrinter(indent=4)

def gif_route(module_dependencies, filename, player):
    os = module_dependencies.os
    subprocess = module_dependencies.subprocess
    flask = module_dependencies.flask
    drawing = module_dependencies.drawing
    logging = module_dependencies.logging
    stats = module_dependencies.stats

    annotation_data = logging.get_annotation_data(filename)
    pp.pprint(["annotation_data keys", annotation_data.keys()])
    print(f"Number of frames: {len(annotation_data['frames'])}")
    print(f"Number of players: {len(annotation_data['tracker_names'])}")
    player_frames = stats.get_player_frames(player, annotation_data)
    images = []

    for index, frame in enumerate(player_frames[:20]):
        output_filename = f"frame_{player}_{index}.png"
        for obj in frame['objects']:
            if obj['tracker_name'] == player:
                xy_upper_left = f"{int(obj['xyxy'][0])},{int(obj['xyxy'][1])}"
                xy_bottom_right = f"{int(obj['xyxy'][2])},{int(obj['xyxy'][3])}"
                image_filename = drawing.crop_image_util(f"{filename}.mp4", xy_upper_left, xy_bottom_right, frame['frame_number'], output_filename=output_filename)
                images.append(image_filename)
                break # out of objects
                

#    output = 'output.mp4'
#    subprocess.call(['ffmpeg', '-i', 'tmp/frame%d.png', '-c:v', 'libvpx-vp9', '-y', output])
    output = f"output_{player}.gif"
    command = ['ffmpeg', '-y', '-i', f"tmp/frame_{player}_%d.png", '-vf', 'setpts=2.0*PTS', '-y', output]
    print(f"Running {command}")
    subprocess.call(command)
    gif_output = flask.send_file(output, mimetype='image/gif')

    for image in images:
        os.remove(image)
    os.remove(output)

    return gif_output

def test_debug():
    deps = mock.Mock()
    deps.os = mock.Mock()
    deps.subprocess = mock.Mock()
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
