import os
import sys
import requests
import time
import zipfile
import json
from urllib.parse import urlparse
from multiprocessing import Pool, Process

from json_standardize import json_standardize

upload_url = 'https://mineru.net/api/v4/file-urls/batch'
api_key = os.environ['MINERU_API_KEY']
header = {
    'Content-Type': 'application/json',
    "Authorization": f"Bearer {api_key}"
}

related_dir = ["./tmp", "./output"]
for dir in related_dir:
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)

def upload_batch_urls(url_name_list, url_list):
    global upload_url, header
    data = {
        "language": "en",
        "files": [
            {"url": url, 'name': url_name, "data_id": "abcd"}
            for url,url_name in zip(url_list, url_name_list)
        ]
    }

    try:
        response = requests.post(upload_url, headers=header, json=data)
        if response.status_code == 200:
            result = response.json()
            print('response success. result:{}'.format(result))
            if result["code"] == 0:
                batch_id = result["data"]["batch_id"]
                print('batch_id:{}'.format(batch_id))
                return batch_id
            else:
                raise Exception('submit task failed,reason:{}'.format(result))
        else:
            raise Exception('response not success. status:{} ,result:{}'.format(response.status_code, response))
    except Exception as err:
        print(err)
        raise err

def upload_batch_files(pdf_name_list, pdf_path_list):
    global upload_url, header
    data = {
        "language": "en",
        "files": [
            {"name": pdf_name, "data_id": "abcd"}
            for pdf_name in pdf_name_list
        ]
    }

    try:
        response = requests.post(upload_url, headers=header, json=data)
        if response.status_code == 200:
            result = response.json()
            print('response success. result:{}'.format(result))
            if result["code"] == 0:
                batch_id = result["data"]["batch_id"]
                urls = result["data"]["file_urls"]
                for url_item, pdf_path_item in zip(urls, pdf_path_list):
                    with open(pdf_path_item, 'rb') as f:
                        res_upload = requests.put(url_item, data=f)
                    if res_upload.status_code == 200:
                        print(f"{pdf_path_item} upload success")
                    else:
                        print(f"{pdf_path_item} upload failed")
                print("all pdf upload successfully")
                return batch_id
            else:
                raise Exception('apply upload url failed,reason:{}'.format(result.msg))
        else:
            raise Exception('response not success. status:{} ,result:{}'.format(response.status_code, response))

    except Exception as err:
        print(err)
        raise err

def monitor_batch(batch_id):
    global header
    monitor_url = f'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
    all_done = False
    full_zip_url_dict = dict()

    # 在每个子进程中创建独立的 Pool
    with Pool(processes=4) as pool:
        while not all_done:
            all_done = True
            res = requests.get(monitor_url, headers=header).json()['data']
            extract_result = res['extract_result']
            for result in extract_result:
                if result['state'] != 'done':
                    all_done = False
                    file_log = f"file_name:{result['file_name']} state: {result['state']}"
                    if result['state'] == 'running':
                        file_log += f" extracted_pages: {result['extract_progress']['extracted_pages']}"
                        file_log += f" total_pages: {result['extract_progress']['total_pages']}"
                    print(file_log)
                    continue
                if result['file_name'] not in full_zip_url_dict:
                    full_zip_url_dict[result['file_name']] = result['full_zip_url']
                    # 使用同步方式处理下载和解压
                    pool.apply_async(download_unzip_standardize, args=(result['full_zip_url'], result['file_name']))
            time.sleep(60)

def run_monitor_batch(batch_id):
    """将 monitor_batch 包装为一个函数，方便并行运行"""
    monitor_batch(batch_id)

def is_url(url):
    # 检查字符串是否是有效的 URL
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def validate_url(url):
    # 检查 URL 是否有效，并且确保它以 .pdf 结尾
    if not url.lower().endswith(".pdf"):
        url += ".pdf"
    
    try:
        response = requests.head(url)
        print("status_code: ", response.status_code)
        return response.status_code in [200, 403], url
    except requests.RequestException:
        return False, url

def validate_path(path):
    """检查路径是否存在，如果不存在则保存并提示"""
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return False
    return True

def get_pdf_files(directory):
    """获取目录下所有 PDF 文件的路径"""
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def download_unzip_standardize(zip_url, target_file_name):
    save_folder = "./tmp"
    file_name = os.path.basename(zip_url)
    save_path = os.path.join(save_folder, file_name)

    try:
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()  # 检查请求是否成功
        
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        extract_folder_suffix = file_name.split(".")[-2]
        extract_folder = os.path.join(save_folder, extract_folder_suffix)
        if not os.path.exists(extract_folder):
            os.makedirs(extract_folder, exist_ok=True)
        with zipfile.ZipFile(save_path, "r") as zip_ref:
            zip_ref.extractall(extract_folder)

        json_path = os.path.join(extract_folder, f"{extract_folder_suffix}_content_list.json")
        json_file = json.load(open(json_path, encoding='utf-8'))
        json_standardize_result = json_standardize(json_file)

        if "Title" in json_standardize_result.keys():
            target_file_name = json_standardize_result['Title'][0]
            special_characters = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in special_characters:
                target_file_name = target_file_name.replace(char, '').split("\n")[0]

        with open(f"./output/{target_file_name}.json", "w", encoding='utf-8') as f:
            json.dump(json_standardize_result, f, ensure_ascii=False, indent=4)
        print(f"文件 {target_file_name} 标准化完成")
        
    except Exception as e:
        print(e)
        raise e
    
def remove_duplicates(pdf_name_list, pdf_path_list, url_name_list, url_list):
    # 去除重复项，同时保持对应关系
    unique_pdf_paths = []
    unique_pdf_names = []
    seen_pdf_paths = set()

    for name, path in zip(pdf_name_list, pdf_path_list):
        if path not in seen_pdf_paths:
            seen_pdf_paths.add(path)
            unique_pdf_names.append(name)
            unique_pdf_paths.append(path)

    unique_urls = []
    unique_url_names = []
    seen_urls = set()

    for name, url in zip(url_name_list, url_list):
        if url not in seen_urls:
            seen_urls.add(url)
            unique_url_names.append(name)
            unique_urls.append(url)

    return unique_pdf_names, unique_pdf_paths, unique_url_names, unique_urls

def mineru_parser(pdf_name_list=None, pdf_path_list=None, url_name_list=None, url_list=None):
    has_files = pdf_name_list is not None and len(pdf_name_list) > 0
    has_url = url_name_list is not None and len(url_name_list) > 0

    if has_files:
        # 分批处理文件，每批 200 个
        batch_size = 200
        for i in range(0, len(pdf_name_list), batch_size):
            batch_names = pdf_name_list[i:i + batch_size]
            batch_paths = pdf_path_list[i:i + batch_size]
            print(f"处理批次: {batch_names}")
            files_batch_id = upload_batch_files(batch_names, batch_paths)
            run_monitor_batch(files_batch_id)  # 同步处理当前批次

    if has_url:
        # 分批处理 URL，每批 200 个
        batch_size = 200
        for i in range(0, len(url_name_list), batch_size):
            batch_names = url_name_list[i:i + batch_size]
            batch_urls = url_list[i:i + batch_size]
            print(f"处理批次: {batch_names}")
            url_batch_id = upload_batch_urls(batch_names, batch_urls)
            run_monitor_batch(url_batch_id)  # 同步处理当前批次
def main():
    # 获取命令行参数（跳过第一个参数，因为它是脚本名称）
    args = sys.argv[1:]

    if not args:
        print("请提供至少一个 PDF 文件、目录或 URL。")
        return

    pdf_name_list = []
    pdf_path_list = []

    url_name_list = []
    url_list = []

    for path in args:
        if is_url(path):
            # 处理 URL
            is_valid, validated_url = validate_url(path)
            if is_valid:
                url_list.append(validated_url)
                url_name_list.append(os.path.basename(validated_url))
            else:
                print(f"忽略无效 URL: {path}")
        else:
            # 处理文件或目录路径
            if not validate_path(path):
                continue

            if os.path.isfile(path) and path.lower().endswith(".pdf"):
                # 单个 PDF 文件
                pdf_name_list.append(os.path.basename(path))
                pdf_path_list.append(path)
            elif os.path.isdir(path):
                # 目录，读取目录下所有 PDF 文件
                pdf_files = get_pdf_files(path)
                for pdf_path in pdf_files:
                    pdf_name_list.append(os.path.basename(pdf_path))
                    pdf_path_list.append(pdf_path)

            else:
                print(f"忽略无效路径或非 PDF 文件: {path}")

    # 去除重复项
    pdf_name_list, pdf_path_list, url_name_list, url_list = remove_duplicates(
        pdf_name_list, pdf_path_list, url_name_list, url_list
    )

    # 打印结果
    print("PDF 文件列表:")
    if len(pdf_name_list) !=0:
        for name, path in zip(pdf_name_list, pdf_path_list):
            print(f"  {name} -> {path}")
    if len(url_name_list) !=0:
        print("URL 列表:")
        for name, url in zip(url_name_list, url_list):
            print(f"  {name} -> {url}")

    mineru_parser(
        pdf_name_list=pdf_name_list,
        pdf_path_list=pdf_path_list,
        url_name_list=url_name_list,
        url_list=url_list
    )


if __name__ == "__main__":
    main()