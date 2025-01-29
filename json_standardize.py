import json
import os
import string
import sys

# 生成1-9的数字列表
digits_list = [str(i) for i in range(1, 10)]

# 生成a-z的字母列表
letters_list = list(string.ascii_lowercase)

def json_standardize(data):
    global digits_list, letters_list
    result = dict()
    last_level_1 = "Title"
    result[last_level_1] = []
    data[0].pop('text_level')
    for item in data:
        if item['type'] != "text":
            continue
        if "text_level" in item.keys():
            last_level_1 = item['text'].strip()
            result[last_level_1] = []
        else:
            result[last_level_1].append(item['text'].strip())

    for key in result.keys():
        value_list = result[key]
        v_result = ""
        for v in value_list:
            if v == "":
                continue
            v_result += v + "\n"
        result[key] = [v_result.strip("\n")]

    new_result = dict()
    last_key = "+"
    for key in result.keys():
        if last_key[0] in digits_list and key[0] == last_key[0]:
            new_result[last_key].append({key: result[key]})
        elif last_key.lower() == "appendix" and key.split(" ")[0].lower() in letters_list:
            new_result[last_key].append({key: result[key]})
        else:
            new_result[key] = result[key]
            last_key = key

    new_result['image'] = []
    new_result['table'] = []
    for item in data:
        if item['type'] == 'image' and len(item['img_caption']) > 0:
            new_result['image'].append(item['img_caption'])
        elif item['type'] == 'table' and len(item['table_caption']) > 0:
            new_result['table'].append(item['table_caption'])
    return new_result

def json_standardize_2(json_data):
    global digits_list, letters_list
    structure = dict()
    data = dict()
    data_idx = 0

    last_level_1 = "Title"
    structure[last_level_1] = []
    if 'text_level' in json_data[0].keys():
        json_data[0].pop('text_level')
    for item in json_data:
        if item['type'] != "text" or item['text'].strip() == "":
            continue
        if "text_level" in item.keys():
            last_level_1 = item['text'].strip()
            structure[last_level_1] = []
        else:
            if len(structure[last_level_1]) == 0:
                structure[last_level_1].append(str(data_idx))
                data[str(data_idx)] = item['text'].strip() +"\n"
                data_idx += 1
            else:
                data[str(data_idx-1)] += item['text'].strip() + "\n"

    for key in data.keys():
        data[key] = data[key].strip("\n")
    
    new_structure = dict()
    last_key = "+"
    for key in structure.keys():
        if last_key[0] in digits_list and key[0] == last_key[0]:
            new_structure[last_key].append({key: structure[key]})
        elif last_key.lower() == "appendix" and key.split(" ")[0].lower() in letters_list:
            new_structure[last_key].append({key: structure[key]})
        else:
            new_structure[key] = structure[key]
            last_key = key

    new_structure['image'] = []
    new_structure['table'] = []
    for item in json_data:
        if item['type'] == 'image' and len(item['img_caption']) > 0:
            item_list = item['img_caption']
            for caption in item_list:
                new_structure['image'].append(str(data_idx))
                data[str(data_idx)] = caption
                data_idx += 1
                continue
        if item['type'] == 'table' and len(item['table_caption']) > 0:
            item_list = item['table_caption']
            for caption in item_list:
                new_structure['table'].append(str(data_idx))
                data[str(data_idx)] = caption
                data_idx += 1
                continue
    result = {
        "structure": new_structure,
        "data": data
    }
    return result

def main(json_path):
    global digits_list, letters_list
    if not json_path.endswith(".json"):
        raise Exception("文件格式错误")
    if not os.path.exists(json_path):
        raise Exception("文件不存在")
    
    data = json.load(open(json_path, 'r', encoding='utf-8'))

    result = json_standardize_2(data)

    if "/" in json_path:
        file_name =  json_path.split("/")[-1]
    elif "\\"in json_path:
        file_name = json_path.split("\\")[-1]
    else:
        raise Exception("文件路径错误")
    if "Title" in result['structure'].keys():
        file_name_idx = result['structure']['Title'][0]
        file_name = result['data'][file_name_idx]
        file_name = file_name.split("\n")[0].strip()
        special_characters = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in special_characters:
            file_name = file_name.replace(char, '')

    output_path = f"./output/{file_name}.json"
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供至少一个 URL 作为参数")
        sys.exit(1)

    json_path = sys.argv[1]
    main(json_path)


