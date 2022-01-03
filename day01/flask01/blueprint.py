from flask import Flask, Blueprint

# blueprint 其实就是django中的app，但是创建过程略微复杂
# 1.创建对象
# 2.定义路由
# 3.注册对象

app = Flask(__name__)
# 创建blueprint对象
bp = Blueprint('bp_test01', __name__)  # 参数一是表示子应用的名称，参数是指明位置


# 定义blueprint的路由 temp 可以接收参数
# @bp.route("/bluetest/<int: temp>")  匹配int
# 
@bp.route("/bluetest/<temp>")
def bluetest(temp):
    return temp


# 在项flask项目中注册blue_print
app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True)
    # app.run()
