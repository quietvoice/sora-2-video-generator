from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, time, json
from datetime import datetime
import threading
from openai import OpenAI
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = "afsjlkajfckjakljcjalksfjlasfafwerc"
app.config['UPLOAD_FOLDER'] = 'generated_videos'
app.config['DATA_FOLDER'] = 'data'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

USERS_FILE = os.path.join(app.config['DATA_FOLDER'], 'users.json')
VIDEOS_FILE = os.path.join(app.config['DATA_FOLDER'], 'videos.json')

def init_data_files():
    for f in [USERS_FILE, VIDEOS_FILE]:
        if not os.path.exists(f):
            with open(f, 'w') as file:
                json.dump({}, file)

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

def get_videos():
    return load_json(VIDEOS_FILE)

def save_videos(videos):
    save_json(VIDEOS_FILE, videos)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_openai_client():
    load_dotenv()
    api_key = os.environ.get('OPENAI_API_KEY', 'FALLBACK OPEN AI KEY HERE')
    print (api_key)
    return OpenAI(api_key=api_key)

def generate_video_background(job_id, prompt, size, duration, user_id):
    videos = get_videos()
    try:
        client = get_openai_client()
        videos[job_id]['status'] = 'starting'
        save_videos(videos)

        video = client.videos.create(model="sora-2", prompt=prompt, size=size, seconds=str(duration))
        videos[job_id]['video_id'] = video.id
        videos[job_id]['status'] = video.status
        save_videos(videos)

        while video.status in ("in_progress", "queued"):
            time.sleep(3)
            video = client.videos.retrieve(video.id)
            videos[job_id]['progress'] = getattr(video, "progress", 0)
            videos[job_id]['status'] = video.status
            save_videos(videos)

        if video.status == "failed":
            videos[job_id]['status'] = 'failed'
            videos[job_id]['error'] = getattr(getattr(video, "error", None), "message", "Unknown error")
            save_videos(videos)
            return

        videos[job_id]['status'] = 'downloading'
        save_videos(videos)

        video_filename = f"{job_id}_video.mp4"
        thumbnail_filename = f"{job_id}_thumbnail.webp"

        content = client.videos.download_content(video.id, variant="video")
        content.write_to_file(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))

        thumbnail = client.videos.download_content(video.id, variant="thumbnail")
        thumbnail.write_to_file(os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename))

        videos[job_id]['status'] = 'completed'
        videos[job_id]['video_path'] = video_filename
        videos[job_id]['thumbnail_path'] = thumbnail_filename
        videos[job_id]['progress'] = 100
        videos[job_id]['completed_at'] = datetime.now().isoformat()
        save_videos(videos)
    except Exception as e:
        videos[job_id]['status'] = 'failed'
        videos[job_id]['error'] = str(e)
        save_videos(videos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html') if 'user_id' not in session else redirect(url_for('index'))

    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    users = get_users()
    if username not in users or not check_password_hash(users[username]['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = username
    session['username'] = users[username]['display_name']
    return jsonify({'success': True, 'redirect': url_for('index')})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html') if 'user_id' not in session else redirect(url_for('index'))

    data = request.json
    username = data.get('username', '').strip().lower()
    display_name = data.get('display_name', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not all([username, display_name, password]):
        return jsonify({'error': 'All fields required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username min 3 chars'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password min 6 chars'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    if not username.isalnum():
        return jsonify({'error': 'Username alphanumeric only'}), 400

    users = get_users()
    if username in users:
        return jsonify({'error': 'Username exists'}), 400

    users[username] = {
        'username': username,
        'display_name': display_name,
        'password': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    }
    save_users(users)

    session['user_id'] = username
    session['username'] = display_name
    return jsonify({'success': True, 'redirect': url_for('index')})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400

    user_id = session['user_id']
    job_id = f"job_{user_id}_{int(time.time() * 1000)}"

    videos = get_videos()
    videos[job_id] = {
        'id': job_id,
        'user_id': user_id,
        'prompt': prompt,
        'size': data.get('size', '1280x720'),
        'duration': data.get('duration', 8),
        'status': 'queued',
        'progress': 0,
        'created_at': datetime.now().isoformat()
    }
    save_videos(videos)

    thread = threading.Thread(target=generate_video_background, 
                             args=(job_id, prompt, data.get('size', '1280x720'), 
                                   data.get('duration', 8), user_id))
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
@login_required
def status(job_id):
    videos = get_videos()
    job = videos.get(job_id)
    if not job:
        return jsonify({'error': 'Not found'}), 404
    if job['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(job)

@app.route('/download/<job_id>/<file_type>')
@login_required
def download(job_id, file_type):
    videos = get_videos()
    job = videos.get(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'error': 'Not ready'}), 404
    if job['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403

    filename = job['video_path'] if file_type == 'video' else job.get('thumbnail_path')
    if not filename:
        return jsonify({'error': 'Invalid type'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True)

@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    videos = get_videos()
    user_videos = [v for v in videos.values() if v.get('user_id') == user_id]
    user_videos.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(user_videos[:50])

@app.route('/delete/<job_id>', methods=['DELETE'])
@login_required
def delete_video(job_id):
    videos = get_videos()
    job = videos.get(job_id)
    if not job:
        return jsonify({'error': 'Not found'}), 404
    if job['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403

    for path_key in ['video_path', 'thumbnail_path']:
        if job.get(path_key):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], job[path_key])
            if os.path.exists(filepath):
                os.remove(filepath)

    del videos[job_id]
    save_videos(videos)
    return jsonify({'success': True})

init_data_files()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
