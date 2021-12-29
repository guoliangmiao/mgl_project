from flask import Flask

#  import_name我们一般会都传入__name__让系统去自动获取入口，如果传入的参数和内件模块名字相同会导致static资源无法访问
app = Flask(__name__)

print(__name__)


@app.route("/")
def hello():
    return "hello world"


if __name__ == "__main__":
    app.run()
