import requests
from lxml import etree
import json
import html
import sys
import re
import time

def getxmlRoot(target):
	#入力されたアクセッション番号から、起点となるxmlをuniprotから読み込む。
	query = 'https://www.uniprot.org/uniprot/'+ target + '.xml'
	response = requests.get(query)
	if response.status_code > 400 or len(str(response.content)) < 10:
		return -1
	return etree.fromstring(response.content)

def xmlTojson_fileoutput(target,depth):
	start = time.time()
	root = getxmlRoot(target)
	if root == -1:
		return -1
	name = root.find('entry/name',root.nsmap).text
	#このdict_がのちにjsonとして返される。
	dict_ = [{"end_num":"","classes":"pydata","comp":{}},{"group":"nodes","classes":"root","data":{"name":name,"id":name}}]
	#すでに相互作用の関係が検出されたタンパク質を記憶しておく
	completion_dict = {"node_num":0,name:["f"]}
	findInteractaion(root,name,0,dict_,depth,completion_dict)
	dict_[0]['comp'] = completion_dict
	print(target + ".json done")
	print(completion_dict)
	print(dict_)
	# arr = dict_[0]['end_num'].split(',')
	# del arr[-1]
	# numarray = list(map(int,arr))
	# print(numarray)
	# for index in numarray:
	# 	print(dict_[index]['data']['name'])
	end = time.time()
	print(format(end-start))
	return json.dumps(dict_,ensure_ascii=True,indent=2)

def xmlTojson_inp_json(json_file,depth):
	start = time.time()
	dict_ = json.loads(str(json_file))
	arr = dict_[0]['end_num'].split(',')
	del arr[-1]
	numarray = list(map(int,arr))
	completion_dict = dict_[0]["comp"]
	print(completion_dict)
	#print(dict_[numarray[1]]['data']['name'])
	for index in numarray:
		target = dict_[index]['ac_num']
		print(target)
		root = getxmlRoot(target)
		if root == -1:
			return -1
		name = dict_[index]['data']['name']
		#completion_dict[name] = []
		findInteractaion(root,name,0,dict_,int(depth),completion_dict)
	print(dict_)
	end = time.time()
	print(format(end-start))
	return json.dumps(dict_,ensure_ascii=True,indent=2)

def findInteractaion(root,name,n,dict_,depth,completion_dict):
	#type属性がinteractionになっているタグを検出
	comment = [com for com in root.findall('entry/comment',root.nsmap) if com.attrib['type'] == 'interaction']
	edges_num = 0
	#debug用の表示
	_n = n + 1
	for i in range(n):
		print(' ',end='')
	print('-------parent: ' + name)
	for elem in comment:
		#interactantには、自分自身のアクセッション番号も記録されている
		intactList = [intact for intact in elem.findall('interactant',root.nsmap)]
		#intactList[0]には、常に自分自身のアクセッション番号が入っている
		intact=intactList[1]
		_id = intact.find('id',root.nsmap)

		#遷移先のタンパク質のxmlファイルを、アクセッション番号(_id.text)から取得する
		child_root = getxmlRoot(_id.text)
		if child_root == -1:
			continue
		child_name = child_root.find('entry/name',root.nsmap).text
		#親と子の名前が一緒ではないなら
		if child_name != name:
			edges_num = edges_num + 1
			#もし解析が完了していないのなら
			#completion_dict[name] = []

			if child_name not in completion_dict[name]:
				completion_dict['node_num'] += 2
				for i in range(_n):
					print('  ',end='')
				print(child_name)
				#子ノードを追加
				node = {"group":"nodes","data":{"name":child_name,"id":child_name},"ac_num":_id.text}
				#親ノードと子ノードを接続
				edges = {"group":"edges","data":{"id":name+str(edges_num),"source":name,"target":child_name}}
				#jsonに追加
				dict_ += [node,edges]
				#親ノードを起点とした相互作用関係リストに子ノードの相互関係を追加
				completion_dict[name] += [child_name]
				completion_dict[child_name] = ["t",name,child_name]
			#ユーザが指定した深さより小さい　かつ まだ子ノードの解析が完了していない
			#if _n < depth and child_name not in completion_dict:
			if _n < depth and completion_dict[child_name][0] == "t":
				#子ノードを起点とした相互作用関係リストを新たに作成
				#completion_dict[child_name] = [name,child_name]
				completion_dict[child_name][0] = "f"
				#子ノードを起点に新たに解析を開始
				findInteractaion(child_root,child_name,_n,dict_,depth,completion_dict)
			else:
				dict_[0]['end_num'] += str(completion_dict['node_num']) + ','
if __name__ == '__main__':	
	#デバッグ用 アクセッション番号と深さをコマンド引数に取る。
	target = str(sys.argv[1])
	depth = int(sys.argv[2])
	filename = target + '.json'
	#同じ階層にファイルを出力
	with open(filename,'w') as f:
		f.write(xmlTojson_fileoutput(target,depth))
	#file1=open(filename,'w')
	#json.dump(xmlTojson_fileoutput(target,depth),file1,ensure_ascii=True,indent=4)
	#file1.close()

	print(target + ".json done")