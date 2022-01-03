from flask import Flask


# 配置文件加载有三种方式：
# 1. 从配置对象中加载
class DefaultConfig(object):
    MYSQL_URL = "127.0.0.1:6379"


#  import_name我们一般会都传入__name__让系统去自动获取入口，如果传入的参数和内件模块名字相同会导致static资源无法访问
app = Flask(__name__)
app.config.from_pyfile('setting.ini')  # 从配置文件中读取
app.config.from_object(DefaultConfig)  # 从配置对象中读取
# silent表示沉默，是否记载到环境变量的配置信息
# 如果True表示沉默，加载不到不报错
# 如果False表示不沉默，加载不到报错
app.config.from_envvar('SET', silent=True)  # 环境变量set指向的是一个配置文件，获取的方式与其他两种相同
print(app.config.get("MYSQL_URL"))


@app.route("/")
def hello():
    return "hello world"


# if __name__ == "__main__":
#     # app.run(debug=True) 开启调试模式运行
#     app.run()
