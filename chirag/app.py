from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask, request, jsonify, render_template
from utils import analyze_image_with_gemini_api, generate_finalized_image_with_sd
from PIL import Image
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    file = request.files['image']
    try:
        image = Image.open(file.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error': 'Invalid image file'}), 400
    improvement_type = request.form.get('improvement_type', 'smart_city')
    suggestions = analyze_image_with_gemini_api(image, improvement_type)
    finalized_image_url = generate_finalized_image_with_sd(image, suggestions)
    return jsonify({'suggestions': suggestions, 'finalized_image_url': finalized_image_url})

if __name__ == '__main__':
    app.run(debug=True) 