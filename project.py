from flask import Flask, request, jsonify, render_template
from PIL import Image
import os
import uuid
import numpy as np
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, 'static', 'outputs')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def merge_images(path_left, path_right, left_pct):
    start_time = time.time() 

    left = Image.open(path_left).convert('RGBA')
    right = Image.open(path_right).convert('RGBA')
    if right.size != left.size:
        right = right.resize(left.size, Image.LANCZOS)

    alpha = float(left_pct) / 100.0
    left_arr = np.array(left, dtype=np.float32)
    right_arr = np.array(right, dtype=np.float32)

    result_arr = left_arr * alpha + right_arr * (1.0 - alpha)
    result_arr = np.clip(result_arr, 0, 255).astype(np.uint8)
    result_img = Image.fromarray(result_arr, 'RGBA')

    exec_time = time.time() - start_time  
    print(f"⏳ merge_images виконано за {exec_time:.3f} сек.")
    return result_img, exec_time

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/merge', methods=['POST'])
def merge_endpoint():
    if 'leftFile' not in request.files or 'rightFile' not in request.files:
        return jsonify({'error':'Missing files'}), 400
    leftf = request.files['leftFile']
    rightf = request.files['rightFile']
    if leftf.filename == '' or rightf.filename == '':
        return jsonify({'error':'No selected file'}), 400
    if not (allowed_file(leftf.filename) and allowed_file(rightf.filename)):
        return jsonify({'error':'Unsupported file type'}), 400

    left_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()) + '_' + secure_filename(leftf.filename))
    right_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()) + '_' + secure_filename(rightf.filename))
    leftf.save(left_path)
    rightf.save(right_path)

    try:
        left_pct = int(request.form.get('leftPct','50'))
        left_pct = max(0, min(100, left_pct))
    except ValueError:
        left_pct = 50

    left_img = Image.open(left_path)
    right_img = Image.open(right_path)

    left_size_kb = os.path.getsize(left_path) / 1024
    right_size_kb = os.path.getsize(right_path) / 1024

   

    merged, exec_time = merge_images(left_path, right_path, left_pct)

    uid = str(uuid.uuid4())
    png_fn = uid+'_merged.png'
    jpg_fn = uid+'_merged.jpg'
    bmp_fn = uid+'_merged.bmp'
    png_path = os.path.join(OUTPUT_DIR, png_fn)
    jpg_path = os.path.join(OUTPUT_DIR, jpg_fn)
    bmp_path = os.path.join(OUTPUT_DIR, bmp_fn)
    merged.save(png_path, 'PNG')
    merged.convert('RGB').save(jpg_path, 'JPEG', quality=90)
    merged.save(bmp_path, 'BMP')
    # 📦 Інформація про результуюче зображення
    result_w, result_h = merged.size
    png_size_kb = os.path.getsize(png_path) / 1024
    jpg_size_kb = os.path.getsize(jpg_path) / 1024
    bmp_size_kb = os.path.getsize(bmp_path) / 1024

    print("\n=== 🖼️ Вхідні зображення ===")
    print(f"Left Image: {left_img.width}x{left_img.height}px | {left_size_kb:.2f} KB")
    print(f"Right Image: {right_img.width}x{right_img.height}px | {right_size_kb:.2f} KB")

    print("=== ✅ Результат ===")
    print(f"Result Resolution: {result_w}x{result_h}px")
    print(f"📁 PNG: {png_size_kb:.2f} KB")
    print(f"📁 JPG: {jpg_size_kb:.2f} KB")
    print(f"📁 BMP: {bmp_size_kb:.2f} KB")

    print(f"⏱ Час виконання merge_images: {exec_time:.3f} сек.")
    print("==============================\n")

   

    return jsonify({
        'png_url': f'/static/outputs/{png_fn}',
        'jpg_url': f'/static/outputs/{jpg_fn}',
        'bmp_url': f'/static/outputs/{bmp_fn}',
        'preview_url': f'/static/outputs/{png_fn}',
    })

@app.route('/demo')
def demo():
    demo1 = '/static/demo/demo1.jpg'
    demo2 = '/static/demo/demo2.jpg'
    return jsonify({
        'left_url': demo1,
        'right_url': demo2
    })

if __name__ == '__main__':
    app.run(debug=True)
