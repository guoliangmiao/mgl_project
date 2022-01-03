from flask import Flask, render_template, redirect

app = Flask(__name__)

"""
flask默认的模板是templates
redirect（‘http://www.baidu.com’） 当url变化的时候把请求转发
"""
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run()
