from flask import Flask, jsonify

app = Flask(__name__)

"""
jsonify会把响应头设置为json
"""
@app.route("/")
def index():
    return jsonify({'name': 'guoliangmiao'})


if __name__ == "__main__":
    app.run()
