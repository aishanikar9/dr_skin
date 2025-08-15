# ngrok_flask_html.py
from flask import Flask, request, render_template_string, jsonify 
from skin_cancer_backend import predict, generate_gpt_response
import os
import base64
from pyngrok import ngrok, conf
# --------------------------
# 1️⃣ Configure ngrok
# --------------------------
NGROK_AUTH_TOKEN = "31KGslGm0xgtj0GQ6NoydsmVhVL_5mAzytc2kJxJhLzB3aSfD"  # Replace with your ngrok token
NGROK_PATH = r"C:\Users\aisha\Downloads\ngrok-v3-stable-windows-amd64\ngrok.exe"        # Path to your manually downloaded ngrok.exe

conf.get_default().ngrok_path = NGROK_PATH
conf.get_default().auth_token = NGROK_AUTH_TOKEN



# --------------------------
# 2️⃣ Flask app setup
# --------------------------
app = Flask(__name__)
last_result = "No current detection"
# --- EMBED LOGO AS BASE64 ---
if os.path.exists("logo.svg"):
    with open("logo.svg", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")
else:
    logo_base64 = ""

# --- MINIMAL HTML UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Doctor Skin</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; }
        header { background: #305cde; color: white; padding: 10px; text-align: center; }
        header img { height: 40px; vertical-align: middle; }
        .container { width: 100%; max-width: 600px; margin: auto; padding: 10px; }
        .section { background: white; padding: 15px; margin-top: 15px; border-radius: 8px; }
        input, button { padding: 8px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px; }
        button { background: #305cde; color: white; border: none; cursor: pointer; }
        button:hover { background: #1e3d9a; }
        #imagePreview { max-width: 100%; margin-top: 10px; border-radius: 6px; display: none; }
        #result { margin-top: 8px; }
        .chat-box { border: 1px solid #ccc; padding: 8px; height: 200px; overflow-y: auto; margin-bottom: 8px; }
        .chat-input { display: flex; gap: 5px; }
        .chat-input input { flex: 1; }
        .user { color: #305cde; font-weight: bold; }
        .bot { color: #1e3d9a; font-weight: bold; }
    </style>
</head>
<body>
<header>
    <h2>Doctor Skin {% if logo_base64 %}<img src="data:image/svg+xml;base64,{{logo_base64}}">{% endif %}</h2>
</header>
<div class="container">

    <div class="section">
        <h3>Upload Skin Image</h3>
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept="image/*">
            <button type="submit">Analyze</button>
        </form>
        <img id="imagePreview">
        <p id="result"></p>
    </div>

    <div class="section">
        <h3>Ask About Your Result</h3>
        <div class="chat-box" id="chatBox"></div>
        <div class="chat-input">
            <input type="text" id="chatInput" placeholder="Ask a question...">
            <button id="chatSend">Send</button>
        </div>
    </div>

</div>

<script>
document.getElementById("fileInput").addEventListener("change", function(){
    const file = this.files[0];
    if (file){
        const reader = new FileReader();
        reader.onload = function(e){
            const img = document.getElementById("imagePreview");
            img.src = e.target.result;
            img.style.display = "block";
        }
        reader.readAsDataURL(file);
    }
});

document.getElementById("uploadForm").addEventListener("submit", function(e){
    e.preventDefault();
    const formData = new FormData(this);
    fetch("/upload", { method: "POST", body: formData })
    .then(res => res.json())
    .then(data => {
        document.getElementById("result").innerText = data.message;
    });
});

document.getElementById("chatSend").addEventListener("click", function(){
    const input = document.getElementById("chatInput");
    const message = input.value.trim();
    if (!message) return;
    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML += `<div><span class="user">You:</span> ${message}</div>`;
    input.value = "";
    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    }).then(res => res.json())
      .then(data => {
        chatBox.innerHTML += `<div><span class="bot">Bot:</span> ${data.message}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
      });
});
</script>
</body>
</html>
"""

# --- ROUTES ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, logo_base64=logo_base64)

@app.route("/upload", methods=["POST"])
def upload_image():
    global last_result
    if "file" in request.files:
        file = request.files["file"]
        if file.filename:
            file_path = f"temp_{file.filename}"
            file.save(file_path)
            try:
                last_result = predict(file_path)
                os.remove(file_path)
                return jsonify({"message": f"You may have: {last_result}"})
            except Exception as e:
                return jsonify({"message": f"Error analyzing image: {e}"})
    return jsonify({"message": "No file uploaded"})

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    try:
        response = generate_gpt_response(user_input, last_result)
        return jsonify({"message": response})
    except Exception as e:
        return jsonify({"message": f"Error generating response: {e}"})

# --------------------------
# 3️⃣ Run app + ngrok
# --------------------------
if __name__ == "__main__":
    port = 4001

    # Start ngrok tunnel
    public_url = ngrok.connect(port)
    print(f" * ngrok tunnel: {public_url}")

    # Run Flask app
    app.run(port=port)