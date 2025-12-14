from flask import Flask

app = Flask(__name__)


from routes.events import events_bp
app.register_blueprint(events_bp, url_prefix='/api/events')


import routes.resources
import routes.allocation
import routes.utilisation

@app.route('/')
def home():
    return "Backend is running"

if __name__ == "__main__":
    app.run(debug=True)