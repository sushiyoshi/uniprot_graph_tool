import requests
from lxml import etree
import json
import html
import sys

def getxmlRoot(target):
	#入力されたアクセッション番号から、起点となるxmlをuniprotから読み込む。
	query = 'https://www.uniprot.org/uniprot/'+ target + '.xml'
	response = requests.get(query)
	if response.status_code > 400 or len(str(response.content)) < 10:
		return -1
	return etree.fromstring(response.content)

def xmlTojson_fileoutput(target,depth):
	root = getxmlRoot(target)
	if root == -1:
		return -1
	name = root.find('entry/name',root.nsmap).text
	#このdict_がのちにjsonとして返される。
	dict_ = [{"group":"nodes","classes":"root","data":{"name":name,"id":name}}]
	#すでに解析が完了しているタンパク質を記憶しておく
	completion_dict = {name:[]}
	findInteractaion(root,name,0,dict_,depth,completion_dict)
	print(target + ".json done")
	print(completion_dict)
	return dict_

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
		intactList = [intact for intact in elem.findall('interactant',root.nsmap)]
		for intact in intactList:
			_id = intact.find('id',root.nsmap)
			#遷移先のタンパク質のxmlファイルを、アクセッション番号(_id.text)から取得する
			child_root = getxmlRoot(_id.text)
			if child_root == -1:
				continue
			child_name = child_root.find('entry/name',root.nsmap).text
			if child_name != name:
				edges_num = edges_num + 1
				if child_name not in completion_dict[name]:
					for i in range(_n):
						print('  ',end='')
					print(child_name)
					node = {"group":"nodes","data":{"name":child_name,"id":child_name}}
					edges = {"group":"edges","data":{"id":name+str(edges_num),"source":name,"target":child_name}}
					dict_ += [node,edges]
					completion_dict[name] += [child_name]
				if _n < depth and _id.text not in completion_dict:
					completion_dict[child_name] = [name,child_name]
					findInteractaion(child_root,child_name,_n,dict_,depth,completion_dict)

if __name__ == '__main__':	
	target = str(sys.argv[1])
	depth = int(sys.argv[2])
	xmlTojson_fileoutput(target,3)