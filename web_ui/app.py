from flask import Flask, render_template, request
import os

app = Flask(__name__)

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
