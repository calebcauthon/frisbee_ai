from flask import Flask, render_template, request
import os
from json_tricks import loads

app = Flask(__name__)

from flask import send_file
import subprocess

# Example route: 
# http://localhost:5000/womens_goalty_10.mp4?xy_upper_left=0,0&xy_bottom_right=100,100&frame_number=1
@app.route('/frame/<filename>', methods=['GET'])
def crop_image(filename):
    xy_upper_left = request.args.get('xy_upper_left')
    xy_bottom_right = request.args.get('xy_bottom_right')
    frame_number = request.args.get('frame_number')

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
    import uuid
    random_filename = str(uuid.uuid4()) + '.png'

    # Construct the ffmpeg command
    command = f"ffmpeg -i static/video_sources/{filename} -vf \"select='eq(n,{frame_number})',crop={width}:{height}:{x1}:{y1},drawbox={drawbox_x}:{drawbox_y}:{drawbox_width}:{drawbox_height}:yellow\" -vframes 1 {random_filename}"

    # Execute the command
    subprocess.run(command, shell=True)

    # Send the file
    response = send_file(random_filename, mimetype='image/png')

    # Delete the file
    os.remove(random_filename)

    return response


@app.route('/api/annotations/<filename>', methods=['GET'])
def get_annotations(filename):
    annotation_file = os.path.join('static', 'annotation_data', f'{filename}_annotation_data.json')
    if not os.path.exists(annotation_file):
        return ""
    with open(annotation_file, 'r') as f:
        annotation_data = loads(f.read())
    return render_template('annotation_data.html', data=annotation_data)


@app.route('/tail')
def tail():
    with open('output.txt', 'r') as f:
        content = f.read()
    return content


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/api/videos/')
def get_videos():
    video_dirs = {
        "source": os.path.join(os.path.dirname(__file__), 'static', 'video_sources'),
        "target": os.path.join(os.path.dirname(__file__), 'static', 'video_targets')
    }
    video_data = {}

    for video_type, video_dir in video_dirs.items():
        video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        video_data[f"{video_type}_video_data"] = [{"full_path": os.path.join(video_dir, f), "filename": f} for f in video_files]

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

    target_video_path = f'static/video_targets/{source_filename}_annotated.mp4'
    command = f"poetry shell && python ../process_video.py --source_video_path static/{source_video_path} --target_video_path {target_video_path}"
    print(f"Running command: {command}")
    import subprocess
    subprocess.Popen(command, shell=True)
    return {"message": "Video processing started"}, 200



if __name__ == '__main__':
    app.run(debug=True)
