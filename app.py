import os
import io
import json
import base64
import tempfile
from flask import Flask, request, jsonify
import pdfplumber
from PIL import Image

app = Flask(__name__)

# Simple shared secret to prevent public access
API_SECRET = os.environ.get('PDF_SERVICE_SECRET', 'changeme')

def check_auth():
    secret = request.headers.get('X-PDF-Secret')
    return secret == API_SECRET


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/process', methods=['POST'])
def process():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    mode = request.form.get('mode', 'full')  # 'count' | 'text' | 'thumbnails' | 'full'
    pages_param = request.form.get('pages', '')  # comma-separated page numbers for full-res
    requested_pages = [int(p) for p in pages_param.split(',') if p.strip().isdigit()]

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            page_count = len(pdf.pages)

            if mode == 'count':
                return jsonify({ 'page_count': page_count })

            # Extract text from all pages
            text_pages = {}
            for i, page in enumerate(pdf.pages):
                try:
                    t = page.extract_text() or ''
                    text_pages[str(i + 1)] = ' '.join(t.split())
                except:
                    text_pages[str(i + 1)] = ''

            if mode == 'text':
                return jsonify({
                    'page_count': page_count,
                    'text': text_pages
                })

            # Generate thumbnails (small, for document mapping)
            safe_token_limit = 47_000
            call1_overhead = 2_500
            tokens_per_page = max(85, min(
                int((safe_token_limit - call1_overhead) / page_count),
                2375
            ))
            pixel_area = tokens_per_page * 750
            import math
            width  = int(math.sqrt(pixel_area / 1.414))
            height = int(width * 1.414)
            dpi    = max(15, round(width / 8.27))

            thumbnails = []
            for page in pdf.pages:
                try:
                    img = page.to_image(resolution=dpi)
                    pil = img.original.copy()
                    pil.thumbnail((width, height), Image.LANCZOS)
                    buf = io.BytesIO()
                    pil.save(buf, format='JPEG', quality=85)
                    thumbnails.append(base64.b64encode(buf.getvalue()).decode())
                except:
                    thumbnails.append('')

            # Generate full-res images for requested pages only
            full_res = {}
            if requested_pages:
                for n in requested_pages:
                    try:
                        page = pdf.pages[n - 1]
                        img  = page.to_image(resolution=150)
                        buf  = io.BytesIO()
                        img.original.save(buf, format='JPEG', quality=90)
                        full_res[str(n)] = base64.b64encode(buf.getvalue()).decode()
                    except:
                        full_res[str(n)] = ''

            return jsonify({
                'page_count':  page_count,
                'text':        text_pages,
                'thumbnails':  thumbnails,
                'full_res':    full_res,
            })

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
