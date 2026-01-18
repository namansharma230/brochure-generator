from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
import os
import uuid
from Brocheture import create_brocheture, markdown_to_styled_pdf, OUTPUT_DIR
import markdown2

load_dotenv(override=True)

app = Flask(__name__)

def sanitize_filename(name):
    return "".join(c for c in name.lower().replace(" ", "_") if c.isalnum() or c in ("_", "-"))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", html=None, download_path=None, error=None)

@app.route("/generate", methods=["POST"])
def generate():
    company = request.form.get("company", "").strip()
    url = request.form.get("url", "").strip()
    if not company or not url or not url.startswith("http"):
        return render_template("index.html", html=None, download_path=None, error="Please provide a valid company name and full URL.")
    try:
        markdown = create_brocheture(company, url)
        html = markdown2.markdown(markdown or "")
        uid = uuid.uuid4().hex[:8]
        safe = sanitize_filename(company)
        filename = f"{safe}_{uid}_brochure.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, filename)
        try:
            markdown_to_styled_pdf(markdown, pdf_path, company)
            download = f"/download/{filename}"
        except Exception:
            download = None
        return render_template("index.html", html=html, download_path=download, error=None, company=company, url=url)
    except Exception as e:
        return render_template("index.html", html=None, download_path=None, error="Failed to generate brochure. Try again.")

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=filename, mimetype="application/pdf")
    return render_template("index.html", html=None, download_path=None, error="File not found.")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
