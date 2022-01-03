from flask import Flask

app = Flask(__name__)

"""
获取url的固定参数：
实例： http://127.0.0.1:5000/user/101
语法：<>
@app.route('/user/<user_id>')
def getuser(user_id):  注意要把<>的值当做形参传递给视图函数
    return user_id

原理是通过flask的转化器，帮我们生成了正则表达式规则（默认有6个转换器any，字符串，整数，浮点数，uuid,path,uniclode）
不满足我我们可以自定义
"""


@app.route('/user/<int:user_id>')
def getuser(user_id):
    print(user_id)
    return str(user_id)

print(app.url_map)
if __name__ == "__main__":
    app.run(debug=True)
