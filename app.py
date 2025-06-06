import os
import cv2
import numpy as np
import onnxruntime as ort
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import time

# --- Basic Flask App Setup ---
app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'database')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
SIMILARITY_THRESHOLD = 0.50

# --- Global Variables for Face Recognition ---
sess = None
input_name = None
face_database = {}


# --- Helper Functions (Face Processing) ---
def preprocess(img_array):
    img = cv2.resize(img_array, (112, 112))
    img = (img.astype(np.float32) - 127.5) / 128.0
    img = img.transpose((2, 0, 1))
    return img[np.newaxis, ...]


def get_embedding(img_array):
    if sess is None: return None
    preprocessed_img = preprocess(img_array)
    output_name = sess.get_outputs()[0].name
    embedding = sess.run([output_name], {input_name: preprocessed_img})[0][0]
    normalized_embedding = embedding / np.linalg.norm(embedding)
    return normalized_embedding


def load_database_from_disk():
    """Scans the upload folder on startup and loads embeddings into memory."""
    global face_database
    print("Loading existing database from disk...")
    start_time = time.time()
    loaded_count = 0
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                img = cv2.imread(filepath)
                if img is None: continue
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                embedding = get_embedding(img_rgb)
                if embedding is not None:
                    face_database[filename] = embedding
                    loaded_count += 1
            except Exception as e:
                print(f"Could not load {filename}: {e}")
    end_time = time.time()
    print(f"Loaded {loaded_count} images in {end_time - start_time:.2f} seconds.")


# --- API Endpoints ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_database', methods=['POST'])
def upload_database():
    """Handles adding images from a folder to the existing database."""
    uploaded_files = request.files.getlist('database_files')
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({'error': 'No files selected for uploading'}), 400

    count = 0
    for file in uploaded_files:
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                img = cv2.imread(filepath)
                if img is None: continue
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                embedding = get_embedding(img_rgb)
                if embedding is not None:
                    face_database[filename] = embedding
                    count += 1
            except Exception as e:
                print(f"Could not process {filename}: {e}")

    return jsonify({
        'message': f'Added {count} new images. Database now contains {len(face_database)} total images.',
        'database_size': len(face_database)
    })


@app.route('/reset_database', methods=['POST'])
def reset_database():
    """Clears the in-memory database and deletes all uploaded files."""
    global face_database
    face_database.clear()

    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    print("Database has been cleared.")
    return jsonify({'message': 'Database has been successfully cleared.'})


@app.route('/find_match', methods=['POST'])
def find_match():
    # This endpoint logic remains the same
    if 'query_image' not in request.files:
        return jsonify({'error': 'No query image part'}), 400
    file = request.files['query_image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not face_database:
        return jsonify({'error': 'Face database is empty. Please upload database images first.'}), 400

    try:
        filestr = file.read()
        npimg = np.frombuffer(filestr, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        query_embedding = get_embedding(img_rgb)

        similar_faces = []
        for filename, db_embedding in face_database.items():
            similarity = np.dot(query_embedding, db_embedding)
            if similarity > SIMILARITY_THRESHOLD:
                similar_faces.append({'filename': filename, 'similarity': float(similarity)})

        sorted_matches = sorted(similar_faces, key=lambda x: x['similarity'], reverse=True)
        return jsonify({'matches': sorted_matches})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500


@app.route('/database_images/<filename>')
def database_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- Main Execution ---
if __name__ == '__main__':
    # Load the ONNX model ONCE
    try:
        model_path = "arcface.onnx"
        sess = ort.InferenceSession(model_path)
        input_name = sess.get_inputs()[0].name
        print(f"ONNX model '{model_path}' loaded successfully.")
        # Load existing images from disk into memory
        load_database_from_disk()
    except Exception as e:
        print(f"CRITICAL: Failed to load ONNX model: {e}")
        sess = None

    app.run(host='0.0.0.0', port=8000, debug=True)