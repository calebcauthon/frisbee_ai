import uuid
from flask import Flask, render_template, request
import os
from json_tricks import loads, dumps
from library import logging, stats, drawing
from web_ui.routes.gif import gif_route
from web_ui.routes.annotations import annotations_route
from types import SimpleNamespace

app = Flask(__name__, static_folder='web_ui/static', template_folder='web_ui/templates')

from flask import send_file
import subprocess
from library import stats
import flask

@app.route('/api/split_tracker_id', methods=['POST'])
def split_tracker_id():
    data = request.get_json()
    tracker_id = int(data['tracker_id'])
    frame_number = int(data['frame_number'])
    video_path = data['video_path']
    logging.split_tracker_id(tracker_id, frame_number, video_path)
    return dumps({'status': 'success'})

@app.route('/frame_stats/<filename>.mp4', methods=['GET'])
def get_frame_stats(filename):
    frame_number = request.args.get('frame', default=1, type=int)
    annotation_data = logging.get_annotation_data(filename)
    frame_data = next((frame for frame in annotation_data['frames'] if frame['frame_number'] == frame_number), None)
    return render_template('frame_stats.html', frame=frame_data)

@app.route('/api/remove_player', methods=['POST'])
def remove_player():
    data = request.get_json()
    player = data['name']
    video_path = data['video_path']
    logging.remove_player(player, video_path)
    return dumps({'status': 'success'})

@app.route('/player_movies/<filename>_<player>.gif', methods=['GET'])
def get_player_movie(filename, player):
    module_dependencies = SimpleNamespace(
        os=os,
        subprocess=subprocess,
        flask=flask,
        drawing=drawing,
        logging=logging,
        stats=stats
    )
    return gif_route(module_dependencies, filename, player)
    
@app.route('/stats/<filename>.mp4', methods=['GET'])
def get_stats(filename):
    annotation_data = logging.get_annotation_data(filename)
    game_data = stats.get_stats(annotation_data)
    return render_template('stats.html', game_data=game_data)

@app.route('/player_stats/<filename>.mp4', methods=['GET'])
def get_player_stats(filename):
    player = request.args.get('player')
    annotation_data = logging.get_annotation_data(filename)
    player_frames = stats.get_frames_with_distance_travelled(player, stats.exclude_other_players(player, stats.get_player_frames(player, annotation_data)))
    return render_template('player_stats.html', frames=player_frames, player=player)

@app.route('/api/add_tracker_name', methods=['POST'])
def add_tracker_name():
    data = request.get_json()
    new_name = data['new_name']
    video_path = data['video_path']
    logging.add_tracker_name(new_name, video_path)
    return dumps({'status': 'success'})

@app.route('/api/change_tracker_name', methods=['POST'])
def change_tracker_name():
    data = request.get_json()
    old_name = data['old_name']
    new_name = data['new_name'] 
    video_path = data['video_path']
    logging.change_tracker_name(old_name, new_name, video_path)
    return dumps({'status': 'success'})

@app.route('/api/move_tracker_id_to_new_name', methods=['POST'])
def change_tracker_id():
    data = request.get_json()
    old_tracker_id = int(data['old_tracker_id'])
    new_name = data['new_name']
    video_path = data['video_path']
    logging.move_tracking_id_to_another_name(old_tracker_id, new_name, video_path)
    return dumps({'status': 'success'})

def crop_image_util(filename, xy_upper_left, xy_bottom_right, frame_number, output_filename=None):
    x1, y1 = map(int, xy_upper_left.split(','))
    x2, y2 = map(int, xy_bottom_right.split(','))

    # Add 20 pixel buffer to the coordinates
    x1 -= 20
    y1 -= 20
    x2 += 20
    y2 += 20

    # Calculate the width and height of the crop
    width = x2 - x1
    height = y2 - y1

    # Calculate the coordinates for the drawbox
    drawbox_x = 20
    drawbox_y = 20
    drawbox_width = width - 40
    drawbox_height = height - 40

    # Generate a random filename
    random_filename = output_filename or str(uuid.uuid4()) + '.png'

    # Construct the ffmpeg command
    if filename in os.listdir('web_ui/static/video_sources'):
        file_path = f"web_ui/static/video_sources/{filename}"
    elif filename in os.listdir('web_ui/static/video_targets'):
        file_path = f"web_ui/static/video_targets/{filename}"
    else:
        raise FileNotFoundError(f"The file {filename} was not found in video_sources or video_targets.")
    command = f"ffmpeg -i {file_path} -vf \"select='eq(n,{frame_number})',crop={width}:{height}:{x1}:{y1},drawbox={drawbox_x}:{drawbox_y}:{drawbox_width}:{drawbox_height}:yellow\" -vframes 1 tmp/{random_filename}"

    # Execute the command
    subprocess.run(command, shell=True)

    return f"tmp/{random_filename}"

# Example route: 
# http://localhost:5000/womens_goalty_10.mp4?xy_upper_left=0,0&xy_bottom_right=100,100&frame_number=1
@app.route('/frame/<filename>', methods=['GET'])
def crop_image(filename):
    xy_upper_left = request.args.get('xy_upper_left')
    xy_bottom_right = request.args.get('xy_bottom_right')
    frame_number = request.args.get('frame_number')

    photo_filename = crop_image_util(filename, xy_upper_left, xy_bottom_right, frame_number)
    response = send_file(photo_filename, mimetype='image/png')
    os.remove(photo_filename)

    return response

# Example URL
# http://localhost:5000/api/annotations/womens_goalty_10.mp4?skip=100&start=1&total_objects=100
@app.route('/api/annotations/<filename>', methods=['GET'])
def get_annotations(filename):
    dependencies = SimpleNamespace(
        logging=logging,
        flask=flask
    )
    return annotations_route(dependencies, filename)

@app.route('/tail')
def tail():
    with open('web_ui/output.txt', 'r') as f:
        content = f.read()
    return content

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/api/videos/')
def get_videos():
    video_dirs = {
        "source": os.path.join(os.path.dirname(__file__), 'web_ui', 'static', 'video_sources'),
        "target": os.path.join(os.path.dirname(__file__), 'web_ui', 'static', 'video_targets')
    }
    video_data = {}

    for video_type, video_dir in video_dirs.items():
        video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        video_data[f"{video_type}_video_data"] = [{
            "full_path": os.path.join(video_dir, f),
            "filename": f,
            "total_frames": stats.get_total_frames(os.path.join(video_dir, f))
        } for f in video_files]

    source_video_data = video_data["source_video_data"]
    target_video_data = video_data["target_video_data"]
    video_data = source_video_data + target_video_data
    return {"videos": video_data}, 200, {'Content-Type': 'application/json'}

@app.route('/api/annotate', methods=['POST'])
def annotate_video():
    data = request.get_json()
    full_path = data.get('path')
    source_video_path = full_path.split('static', 1)[-1]
    if source_video_path.startswith('//'):
        source_video_path = source_video_path[1:]

    source_filename = os.path.basename(source_video_path)
    source_filename = os.path.splitext(source_filename)[0]
    print(f"source_filename: {source_filename} from source_video_path: {source_video_path}")

    target_video_path = f'web_ui/static/video_targets/{source_filename}_annotated.mp4'
    command = f"poetry shell && python process_video.py --source_video_path web_ui/static/{source_video_path} --target_video_path {target_video_path}"
    print(f"Running command: {command}")
    import subprocess
    subprocess.Popen(command, shell=True)
    return {"message": "Video processing started"}, 200

if __name__ == '__main__':
    app.run(debug=True)
