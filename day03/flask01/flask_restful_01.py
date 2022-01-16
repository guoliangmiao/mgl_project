#  flask-restful是一个扩展包，用来在flask中实现restful风格的接口
"""
基本使用：
1.pip install flask-restful
2. from flask_restful import Api,Resource
3. 定义视图类，必须继承Resource
4. 定义请求方法
5. 定义路由
"""

from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)

api = Api(app)  # 实例化Api对象


class Index(Resource):
    #  flask-restful会自动把return默认转为josn
    def get(self):
        return "helloworld"


api.add_resource(Index, '/', endpoint='index')  # endpoint给视图起名字，默认和类视图同名

if __name__ == "__main__":
    app.run()
