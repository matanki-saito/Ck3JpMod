import os
import re
import shutil
from os.path import join
import requests
from pathlib import Path

_ = join


def jp_filter(src, dst):
	if re.search(r"l_japanese.yml$", src):
		shutil.copy2(src, dst)


def en_filter(src, dst):
	if re.search(r"l_english.yml$", src):
		shutil.copy2(src, dst)


def update_file(base_path, source_path, project_id, secret, base_url="https://paratranz.cn"):
	# https://paratranz.cn/api/projects/5456/files
	# POST
	# arg1 : file : binary
	# arg2 : path: /clausewitz/text_utils
	# Content-Type: multipart/form-data;
	# Content-Length: 751

	file_name = os.path.basename(source_path)
	file_data_binary = open(source_path, 'rb').read()
	files = {
		'file': (file_name, file_data_binary,  'application/json; charset=utf-8'),
		'path': "/" + str(Path(source_path).relative_to(Path(base_path)).parent)
	}

	url = "{}/api/projects/{}/files".format(base_url, project_id)
	headers = {'Authorization': secret}
	response = requests.post(url, files=files, headers=headers)

	print(response)


def main():
	extract_path = Path("./extract")
	shutil.rmtree(extract_path, ignore_errors=True)
	os.makedirs(extract_path, exist_ok=True)

	base_path = Path("./tmp/game/steamapps/common/Crusader Kings III")

	shutil.copytree(base_path.joinpath(Path("game", "localization", "english")), extract_path.joinpath(Path("game", "localization", "english")))
	shutil.copytree(base_path.joinpath(Path("jomini", "localization")), extract_path.joinpath(Path("jomini", "localization")), copy_function=en_filter)
	shutil.copytree(base_path.joinpath(Path("clausewitz", "localization")), extract_path.joinpath(Path("clausewitz", "localization")), copy_function=en_filter)

	# update_file(
	# 	base_path=converted_root_path,
	# 	source_path=_(converted_root_path, "clausewitz", "cw_tools_l_english.json"),
	# 	secret=os.environ.get("PARATRANZ_SECRET"),
	# 	project_id=5456)


if __name__ == "__main__":
	# execute only if run as a script
	main()
