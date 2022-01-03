from flask import Flask, request

app = Flask(__name__)
"""
使用request获取参数：
http://127.0.0.1:5000/?user_id=101
request.args.get('user_id')

如果是表单提交的post请求：
request.form.get('password')
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    return request.args.get('user_id')


if __name__ == "__main__":
    app.run(debug=True)
