from flask import Flask, Blueprint
# 蓝图（其实就是项目子应用app）和restful的使用
# 蓝图的使用步骤 1.创建蓝图 2.定义蓝图路由 3，注册蓝图对象
from flask_restful import Api, Resource

app = Flask(__name__)
index_dp = Blueprint('index_dp', __name__)  # index_dp蓝图名称

api = Api(index_dp)  # 把蓝图(子应用)对象当做参数，实例化Api对象


class IndexResource(Resource):
    def get(self):
        return "helloworld"


app.register_blueprint(index_dp)  # 注册蓝图
api.add_resource(IndexResource, '/', endpoint="indexresource")  # 添加蓝图路由

if __name__ == "__main__":
    api.run(debug=True)
