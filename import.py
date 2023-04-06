import json
import os
import pathlib
from os.path import join
from pathlib import Path
from typing import List

import requests

_ = join


class Context:
    secret: str = os.environ.get("PARATRANZ_SECRET")
    project_id: int = 1518
    extract_path: Path = Path("extract")
    paratranz_zip_file: Path = Path("tmp/p.zip")
    base_url: str = "https://paratranz.cn"


class Context2:
    context: Context = None
    file_paths: List[str] = []
    paradox_file_name_to_id_map: dict = {}

    def __init__(self, context: Context,
                 file_paths: List[str],
                 paradox_file_name_to_id_map: dict):
        self.context = context
        self.file_paths = file_paths
        self.paradox_file_name_to_id_map = paradox_file_name_to_id_map


def get_extract_file_paths(ctx: Context):
    result: List[str] = []
    for file_path in pathlib.Path(ctx.extract_path).glob('**/*.yml'):
        pure_path = str(file_path.relative_to(ctx.extract_path)).replace("\\", "/")
        result.append(pure_path)

    return result


def get_file_infos(context: Context):
    # https://paratranz.cn/api/projects/5456/files
    # GET

    url = "{}/api/projects/{}/files".format(context.base_url, context.project_id)
    headers = {'Authorization': context.secret}
    response = json.loads(requests.get(url, headers=headers).text)

    result = {}
    for record in response:
        result[record["name"]] = record["id"]

    return result


def update_current_file(file_id: int, source_path: Path, context: Context):
    file_name = source_path.name
    file_data_binary = open(source_path, 'rb').read()
    files = {
        'file': (file_name, file_data_binary, 'application/json; charset=utf-8')
    }

    print("[LOG] Update file, id={}, path={}".format(file_id, str(source_path)))

    url = "{}/api/projects/{}/files/{}".format(context.base_url, context.project_id, file_id)
    headers = {'Authorization': context.secret}
    response = requests.post(url, files=files, headers=headers)

    print("[LOG] status code {}".format(response.status_code))


def add_new_file(base_path: Path, source_path: Path, context: Context):
    file_name = source_path.name
    file_data_binary = open(source_path, 'rb').read()
    data = {'path': str(Path("/").joinpath(source_path.relative_to(base_path).parent)).replace("\\", "/")}
    files = {
        'file': (file_name, file_data_binary, 'application/yaml; charset=utf-8')
    }

    print("[LOG] Add new file, file_name={}".format(file_name))

    url = "{}/api/projects/{}/files".format(context.base_url, context.project_id)
    headers = {'Authorization': context.secret}
    response = requests.post(url, files=files, data=data, headers=headers)

    print("[LOG] status code {}".format(response.status_code))


def update_files(ctx: Context2):
    for file_path in ctx.file_paths:

        if file_path not in ctx.paradox_file_name_to_id_map:
            print("new", file_path)
            add_new_file(
                base_path=ctx.context.extract_path,
                source_path=Path(ctx.context.extract_path).joinpath(file_path),
                context=ctx.context)
        else:
            print("update", file_path)
            update_current_file(
                file_id=ctx.paradox_file_name_to_id_map[file_path],
                source_path=Path(ctx.context.extract_path).joinpath(file_path),
                context=ctx.context)

    # TODO: delete files


def main():
    os.makedirs("tmp", exist_ok=True)
    context: Context = Context()
    context2: Context2 = Context2(context=context,
                                  file_paths=get_extract_file_paths(context),
                                  paradox_file_name_to_id_map=get_file_infos(context))
    update_files(context2)


if __name__ == "__main__":
    main()
