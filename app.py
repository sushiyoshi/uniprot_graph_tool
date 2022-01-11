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

# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['json'])

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/graph",methods=['GET', 'POST'])
def graph():
    try:
        #アクセッション番号からグラフを生成する場合は、GET
        if request.method == 'GET':
            #アクセッション番号
            target = request.args.get('query', '')
            #深さ
            depth = request.args.get('depth', '')
            return render_template("loading.html",query=target,depth=depth)
        #アップロードしたjsonファイルからグラフを生成する場合は、POST
        elif request.method == 'POST':
            global elements
            if 'fileup' not in request.files:
                return 'file unspecified'
            file = request.files['fileup']
            if file.filename == '':
                return 'file unspecified'
            if file and allwed_file(file.filename):
                filename = secure_filename(file.filename)
                #fileはFileSrage型なので、readしてjsonに変換
                print(file)
                elements = json.dumps(json.loads(file.read()))
                print(elements)
                return render_template("graph.html",elem=elements,filename=filename)
            else:
                return 'file error'
        else:
            return abort(400)
    except Exception as e:
        return str(e)

@app.route("/analyze",methods=['GET', 'POST'])
def analyze():
    global elements
    #アクセッション番号
    target = request.args.get('query', '')
    #深さ
    depth = request.args.get('depth', '')
    filename = target + '.json'
    elements = xml_to_json.xmlTojson_fileoutput(target,int(depth))
    print(elements)
    #無効なアクセッション番号
    if elements == -1:
        return 'Invalid accession number'
    return render_template("graph.html",elem=elements,filename=filename)


@app.route('/download',methods=['GET','POST'])
def donwload():
    #ファイル名はダウンロードボタンに記載してある
    filename = request.args.get('button', '')
    #ファイルをサーバ内に残さないために、インメモリでjsonファイルの内容を展開
    mem = io.BytesIO()
    print(elements)
    mem.write( elements.encode('utf-8'))
    mem.seek(0)
    #ユーザーに処理したjsonファイルを送信する
    return send_file( mem, mimetype='application/json', as_attachment=True, attachment_filename=filename)

if __name__ == "__main__":
    app.run(debug=True)