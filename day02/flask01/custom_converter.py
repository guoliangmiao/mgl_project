from flask import Flask
from werkzeug.routing import BaseConverter

"""
1.自定义类，继承baseconverter类
2.把自定以转换器添加到转换器字典中
3.在路由装饰器中使用
"""
app = Flask(__name__)


class PhoneNumConverter(BaseConverter):
    regex = r'1[3-9]\d{9}'


app.url_map.converters['mobile'] = PhoneNumConverter


@app.route('/<mobile:num>')
def get_phone_num(num):
    return num


if __name__ == "__main__":
    app.run()
