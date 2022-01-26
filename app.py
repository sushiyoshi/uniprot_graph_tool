# -*- coding: utf-8 -*-
import os
import json
from flask import Flask, render_template, request,redirect,url_for,send_file
import sys
import xml_to_json
from werkzeug.utils import secure_filename
from flask import send_from_directory
import tempfile
import io

app = Flask(__name__)
global elements
elements = {}

# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['json'])
def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    print(elements)
    return render_template("index.html")

# @app.route("/graph",methods=['GET', 'POST'])
# def graph():
#     try:
#         #アクセッション番号からグラフを生成する場合は、GET
#         if request.method == 'GET':
#             #アクセッション番号
#             target = request.args.get('query', '')
#             #深さ
#             depth = request.args.get('depth', '')
#             return render_template("loading.html",query=target,depth=depth)
#         #アップロードしたjsonファイルからグラフを生成する場合は、POST
#         elif request.method == 'POST':
#             global elements
#             if 'fileup' not in request.files:
#                 return 'file unspecified'
#             file = request.files['fileup']
#             if file.filename == '':
#                 return 'file unspecified'
#             if file and allwed_file(file.filename):
#                 filename = secure_filename(file.filename)
#                 #fileはFileSrage型なので、readしてjsonに変換
#                 elements[filename] = json.dumps(json.loads(file.read()))
#                 print(elements[filename])
#                 return render_template("graph.html",elem=elements[filename],filename=filename)
#             else:
#                 return 'file unspecified'
#         else:
#             return abort(400)
#     except Exception as e:
#         return str(e)

@app.route("/analyze_mode",methods=['GET'])
def analyze_mode():
    try:
        #アクセッション番号からグラフを生成する場合は、GET
        if request.method == 'GET':
            #アクセッション番号
            target = request.args.get('query', '')
            #深さ
            depth = request.args.get('depth', '')
            return render_template("loading.html",query=target,depth=depth)
        else:
            return render_template("error.html",error_text=abort(400))
    except Exception as e:
        return render_template("error.html",error_text=(str(e)))

@app.route("/analyze",methods=['GET'])
def analyze():
    global elements
    #アクセッション番号
    target = request.args.get('query', '')
    #深さ
    depth = request.args.get('depth', '')
    filename = target + '.json'
    elements[filename] = xml_to_json.xmlTojson_fileoutput(target,int(depth))
    #無効なアクセッション番号
    if elements[filename] == -1:
        return render_template("error.html",error_text='Invalid accession number')
    return render_template("graph.html",elem=elements[filename],filename=filename)

@app.route("/file_mode",methods=['POST'])
def file_mode():
    try:
    #アップロードしたjsonファイルからグラフを生成する場合は、POST
        if request.method == 'POST':
            depth = request.form.get("depth")
            global elements
            if 'fileup' not in request.files:
                return render_template("error.html",error_text='file unspecified')
            file = request.files['fileup']
            if file.filename == '':
                return render_template("error.html",error_text='file unspecified')
            if file and allwed_file(file.filename):
                filename = secure_filename(file.filename)
                #fileはFileSrage型なので、readしてjsonに変換
                json_file = json.dumps(json.loads(file.read()))
                depth = int(depth)
                if depth != 0:
                    json_file = xml_to_json.xmlTojson_inp_json(json_file,depth)
                elements[filename] = json_file
                #print(elements[filename])
                return render_template("graph.html",elem=elements[filename],filename=filename)
            else:
                return render_template("error.html",error_text='file unspecified')
        else:
            return abort(400)
    except Exception as e:
        return str(e)

@app.route('/download',methods=['GET','POST'])
def donwload():
    #ファイル名はダウンロードボタンに記載してある
    filename = request.args.get('button', '')
    file = elements[filename]
    if file:
        #ファイルをサーバ内に残さないために、インメモリでjsonファイルの内容を展開
        mem = io.BytesIO()
        mem.write( file.encode('utf-8'))
        mem.seek(0)
        #ユーザーに処理したjsonファイルを送信する
        return send_file( mem, mimetype='application/json', as_attachment=True, attachment_filename=filename)
    else:
        return render_template("error.html",error_text='This file may have been invalidated because the timeout period has elapsed.')
if __name__ == "__main__":
    app.run(debug=True)