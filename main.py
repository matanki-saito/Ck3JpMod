#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import pathlib
import shutil
import textwrap
import time
import urllib.request
import zipfile
from os.path import join

import regex

_ = join


def download_trans_zip_from_paratranz(project_id,
                                      secret,
                                      out_file_path,
                                      base_url="https://paratranz.cn"):
    """
    paratranzからzipをダウンロードする。ダウンロード前にre-generateする
    :param project_id:
    :param secret:
    :param base_url:
    :param out_file_path:
    :return:
    """

    regenerate_request_url = "{}/api/projects/{}/artifacts".format(base_url, project_id)
    req = urllib.request.Request(regenerate_request_url, method="POST")
    req.add_header("Authorization", secret)
    with urllib.request.urlopen(req) as response:
        print(response.read().decode("utf-8"))

    # wait for regenerate
    time.sleep(90)

    download_request_url = "{}/api/projects/{}/artifacts/download".format(base_url, project_id)
    req = urllib.request.Request(download_request_url)
    req.add_header("Authorization", secret)

    with open(out_file_path, "wb") as my_file:
        my_file.write(urllib.request.urlopen(req).read())

    return out_file_path


def assembly_mod(mod_file_name,
                 resource_dir_path,
                 resource_paratranz_main_zip_file_path,
                 out_dir_path):
    """
    Appモッドを作成
    :param mod_file_name: Modファイル名
    :param resource_paratranz_main_zip_file_path: ParatranzからダウンロードできるMain Mod zipファイルのパス
    :param resource_dir_path: リソースディレクトリパス
    :param out_dir_path: 出力フォルダ
    :return:
    """

    ext_paratranz_main_dir_path = _(".", "tmp", "paratranz_ext_main")
    mod_dir_path = _(out_dir_path, mod_file_name)
    mod_loc_root_dir_path = _(mod_dir_path, "localization")
    mod_loc_replace_dir_path = _(mod_loc_root_dir_path, "replace")

    # 初期化（github-actionsでは必要ない）
    if os.path.exists(ext_paratranz_main_dir_path):
        shutil.rmtree(ext_paratranz_main_dir_path)
    if os.path.exists(mod_dir_path):
        shutil.rmtree(mod_dir_path)
    os.makedirs(mod_dir_path, exist_ok=True)
    os.makedirs(mod_loc_replace_dir_path, exist_ok=True)

    # zip展開する
    with zipfile.ZipFile(resource_paratranz_main_zip_file_path) as existing_zip:
        existing_zip.extractall(ext_paratranz_main_dir_path)

    # 画像ファイルを入れる
    shutil.copy(_(resource_dir_path, "title.jpg"), mod_dir_path)

    # clausewitzを移す
    shutil.copytree(_(ext_paratranz_main_dir_path, "utf8", "clausewitz", "localization"),
                    _(mod_loc_replace_dir_path, "clausewitz"))

    # jominiを移す
    # trigger_system_l_englishが入っていると一部の環境で表示が不正になるため除外した
    # https://discord.com/channels/439564919072096276/739722048691109888/983636821818871819
    jomini_dir = _(mod_loc_replace_dir_path, "jomini")
    shutil.copytree(src=_(ext_paratranz_main_dir_path, "utf8", "jomini", "localization"),
                    dst=jomini_dir, ignore=shutil.ignore_patterns("trigger_system_l_english.yml"))

    fix_ISSUE_1(path=jomini_dir)

    # gameを移す
    game_dir = _(mod_loc_root_dir_path, "english")
    shutil.copytree(src=_(ext_paratranz_main_dir_path, "utf8", "game", "localization", "english"),
                    dst=game_dir)
    # japanese_mod(path=game_dir)

    # 特別なファイルを移す ISSUE #1 参照
    game_replace_dir_path = _(mod_loc_replace_dir_path, "game")
    os.makedirs(game_replace_dir_path, exist_ok=True)
    shutil.copy(_(resource_dir_path, "japanese_l_english.yml"), game_replace_dir_path)

    # descriptor.modを置く
    generate_descriptor_mod_file(mod_dir_path, os.environ.get("RUN_NUMBER"), "1.17.*", 2217567218)

    return mod_dir_path


def generate_descriptor_mod_file(target_path, mod_version, game_version, remote_file_id):
    text = textwrap.dedent("""\
        version="1.%s"
        name="Japanese Language Mod"
        tags={
        "Translation"
        "Localization"
        }
        supported_version="%s"
        remote_file_id="%d"
    """ % (mod_version, game_version, remote_file_id))

    with open(_(target_path, 'descriptor.mod'), 'wt') as fw:
        fw.write(text)


def generate_dot_mod_file(mod_title_name,
                          mod_dir_name,
                          mod_tags,
                          mod_image_file_path,
                          mod_supported_version,
                          out_dir_path):
    """
    .modファイルを作る
    :param mod_title_name:
    :param mod_dir_name: ディレクトリの名前
    :param mod_tags: Set<String>型
    :param mod_image_file_path:
    :param mod_supported_version:
    :param out_dir_path: 出力ディレクトリのパス
    :return: 出力ファイルパス
    """

    os.makedirs(out_dir_path, exist_ok=True)

    out_file_path = _(out_dir_path, "{}.mod".format(mod_dir_name))

    with open(out_file_path, "w", encoding="utf-8") as fw:
        lines = [
            'name="{}"'.format(mod_title_name),
            'path="mod/{}"'.format(mod_dir_name),
            'tags={}'.format("{" + " ".join(map(lambda c: '"{}"'.format(c), mod_tags)) + "}"),
            'supported_version="{}"'.format(mod_supported_version),
            'picture="{}"'.format(mod_image_file_path)
        ]

        fw.write("\n".join(lines))

    return out_file_path


p = regex.compile(r"([ぁ-んァ-ヶ一-龥ー。、「」？！](?![ー？！。、「」]))")


def japanese_mod(path):
    for file_path in pathlib.Path(path).glob('**/*.yml'):
        with open(file_path, 'r', encoding="utf_8_sig") as fr:
            txt = p.sub(repl=r"\1 ", string=fr.read())

        with open(file_path, 'w', encoding="utf_8_sig") as fw:
            fw.write(txt)


p2 = regex.compile(r"\s(POSSESSIVE_CHECK|POSSESSIVE_SPECIAL|POSSESSIVE_GENERAL):([0-9]+)\s\"[^\"]+\"")


def fix_ISSUE_1(path):
    for file_path in pathlib.Path(path).glob('**/script_system_l_english.yml'):
        with open(file_path, 'r', encoding="utf_8_sig") as fr:
            txt = p2.sub(repl=r' \1:\2 ""', string=fr.read())

        with open(file_path, 'w', encoding="utf_8_sig") as fw:
            fw.write(txt)


def update_source(mod_folder_path):
    shutil.rmtree("source/", ignore_errors=True)
    shutil.copytree(mod_folder_path, _("source"))


def main():
    # 一時フォルダ用意
    os.makedirs(_(".", "tmp"), exist_ok=True)
    os.makedirs(_(".", "out"), exist_ok=True)
    out_dir_path = _(".", "out")
    zip_path = _(".", "tmp", "paratranz_main.zip")

    # main name
    mod_file_name = "japaneselang"

    # 翻訳の最新版をダウンロードする project_id=1518はCKIII JPのプロジェクトID
    if not os.path.exists(zip_path):
        p_file_main_path = download_trans_zip_from_paratranz(
            project_id=1518,
            secret=os.environ.get("PARATRANZ_SECRET"),
            out_file_path=zip_path)
        print("p_file_main_path:{}".format(p_file_main_path))
    else:
        p_file_main_path = zip_path

    # Modを構築する（フォルダのまま）
    mod_folder_path = assembly_mod(
        mod_file_name=mod_file_name,
        resource_paratranz_main_zip_file_path=p_file_main_path,
        resource_dir_path=_(".", "resource"),
        out_dir_path=out_dir_path)
    print("mod_dir_path:{}".format(out_dir_path))

    # utf8ファイルを移動する（この後git pushする）
    update_source(mod_folder_path=mod_folder_path)


if __name__ == "__main__":
    main()
