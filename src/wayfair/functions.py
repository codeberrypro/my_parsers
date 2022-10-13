import json
import os
import time


def trying(function, max_attempts=3):
    # Function attempts
    out = 0
    attempts = 0
    while out == 0:
        attempts += 1
        if attempts > max_attempts:
            return 0
        out = function()
        if out == 0:
            time.sleep(3)
    return out


def check_dir(dir_check=None):
    # Checking if a directory exists
    if not dir_check:
        dir_check = "files"
    if not os.path.exists(dir_check):
        os.mkdir(dir_check)


def check_file(file_name, is_dict=None):
    # Checking if a file exists
    check_dir()
    if os.path.isfile("files/%s" % file_name):
        return 0
    with open("files/%s" % file_name, "w", encoding="UTF-8") as f:
        if is_dict:
            text_to_create_file = "{}"
        else:
            text_to_create_file = ""
        f.write(text_to_create_file)
        return 0


def get_file(file_name, is_dict=None, is_list=None, path=True):
    # Getting information from a file
    if path:
        path = "files/"
        check_file(file_name, is_dict)
    else:
        path = ""
    if not is_dict and not is_list:
        with open(f"{path}%s" % file_name, "r", encoding="utf-8") as f:
            return f.read()

    with open(f"{path}%s" % file_name, "r", encoding="utf-8") as f:
        if is_dict:
            try:
                data_read = f.read()
                return json.loads(data_read)
            except:
                return {}
        data_read = f.readlines()
        if not data_read:
            print(f"File {path}%s  is empty" % file_name)
            if is_list:
                return []
            return ""
        return [line.rstrip() for line in data_read]


def save_file(file_name, data_to_save, is_dict=None, is_add=None, is_list=None, path=True):
    # Saving a file
    if path:
        path = "files/"
        check_file(file_name, is_dict)
    else:
        path = ""
    if is_dict:
        with open(f"{path}%s" % file_name, "w", encoding='utf-8') as f:
            f.write(json.dumps(data_to_save, indent=4))
    elif is_add:
        with open(f"{path}%s" % file_name, "a", encoding='utf-8') as f:
            f.write("%s\n" % data_to_save)
    elif is_list:
        with open(f"{path}%s" % file_name, "w", encoding='utf-8') as f:
            [f.write("%s\n" % line) for line in data_to_save]
    else:
        with open(f"{path}%s" % file_name, "w", encoding='utf-8') as f:
            f.write(data_to_save)
