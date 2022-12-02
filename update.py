import glob
import json
import os
from os.path import join
import requests
from pathlib import Path

_ = join


def get_file_infos(project_id, secret, base_url="https://paratranz.cn"):
    # https://paratranz.cn/api/projects/5456/files
    # GET

    url = "{}/api/projects/{}/files".format(base_url, project_id)
    headers = {'Authorization': secret}
    response = json.loads(requests.get(url, headers=headers).text)

    result = {}
    for record in response:
        result[record["name"]] = record["id"]

    return result


def update_old_file(file_id, source_path: Path, project_id, secret, base_url="https://paratranz.cn"):
    # https://paratranz.cn/api/projects/5456/files
    # POST
    # arg1 : file : binary
    # arg2 : path: /clausewitz/text_utils
    # Content-Type: multipart/form-data;
    # Content-Length: 751

    file_name = source_path.name
    file_data_binary = open(source_path, 'rb').read()
    files = {
        'file': (file_name, file_data_binary,  'application/json; charset=utf-8')
    }

    url = "{}/api/projects/{}/files/{}".format(base_url, project_id, file_id)
    headers = {'Authorization': secret}
    response = requests.post(url, files=files, headers=headers)

    print("update.yml")
    print(response)


def update_new_file(base_path: Path, source_path: Path, project_id, secret, base_url="https://paratranz.cn"):
    # https://paratranz.cn/api/projects/5456/files
    # POST
    # arg1 : file : binary
    # arg2 : path: /clausewitz/text_utils
    # Content-Type: multipart/form-data;
    # Content-Length: 751

    file_name = source_path.name
    file_data_binary = open(source_path, 'rb').read()
    files = {
        'file': (file_name, file_data_binary,  'application/json; charset=utf-8'),
        'path': str(Path("/").joinpath(source_path.relative_to(base_path).parent)).replace("\\", "/")
    }

    url = "{}/api/projects/{}/files".format(base_url, project_id)
    headers = {'Authorization': secret}
    response = requests.post(url, files=files, headers=headers)

    print("new")
    print(response)


def main():
    secret = os.environ.get("PARATRANZ_SECRET")
    project_id = 1518

    name2id = get_file_infos(secret=secret, project_id=project_id)

    ext_path = Path("extract")
    for f in ext_path.glob("**/*.yml"):
        print(f)
        pure = str(f.relative_to(ext_path)).replace("\\", "/")

        if pure not in name2id:
            update_new_file(
                base_path=ext_path,
                source_path=f,
                secret=secret,
                project_id=project_id)
        else:
            update_old_file(
                file_id=name2id[pure],
                source_path=f,
                secret=secret,
                project_id=project_id)


if __name__ == "__main__":
    # execute only if run as a script
    main()
