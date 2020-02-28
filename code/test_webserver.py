from flask import Flask
app = Flask(__name__)

# Route all URLs back to this handler
@app.route('/', defaults={'path':''})
@app.route('/<path:path>')
def hello(path):
    return f'Hello, your path is: {path}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
