from flask import Flask
import threading
import time

app = Flask(__name__)

@app.route("/")
def home():
    return "Background worker running!"

def background_task():
    while True:
        # Your background task logic here
        print("Background task is running...")
        time.sleep(10)  # Simulating work with a delay

if __name__ == "__main__":
    # Start the background task in a separate thread
    threading.Thread(target=background_task, daemon=True).start()
    
    # Run the Flask app (Render requires the service to bind to a port)
    app.run(host="0.0.0.0", port=8000)
