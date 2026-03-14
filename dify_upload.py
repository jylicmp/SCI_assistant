"""
知识库操作
"""
import requests, os, json
import logging
import glob
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 日志：同时输出到控制台和当前目录下的 log 文件
def _setup_logging():
    log_path = os.path.join(os.getcwd(), 'dify_upload.log')
    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    root = logging.getLogger()
    if not root.handlers:
        root.setLevel(logging.INFO)
        h_file = logging.FileHandler(log_path, encoding='utf-8')
        h_file.setFormatter(logging.Formatter(fmt))
        h_console = logging.StreamHandler()
        h_console.setFormatter(logging.Formatter(fmt))
        root.addHandler(h_file)
        root.addHandler(h_console)
    return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# Configuration from environment variables
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://8.163.22.1/v1")
KNOWLEDGE_BASE_ID = os.getenv("DIFY_KNOWLEDGE_BASE_ID")
DOC_DIR = os.getenv("DOC_DIR", '/Users/lijiayu/Documents/Literature')
DOC_SUFFIX = os.getenv("DOC_SUFFIX", "pdf")
"""
上传文档到知识库
"""
def upload_doc(file_path, file_name=None):
    """
    上传文件到Dify知识库

    :param file_path: 本地文件路径
    :param file_name: 可选，自定义文件名
    :return: API响应
    """
    if file_name is None:
        file_name = os.path.basename(file_path)

    url = f"{DIFY_BASE_URL}/datasets/{KNOWLEDGE_BASE_ID}/document/create-by-file"

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
    }

    #new_data = {"indexing_technique":"high_quality","process_rule":{"rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":True},{"id":"remove_urls_emails","enabled":True}],"segmentation":{"separator":"###","max_tokens":500}},"mode":"custom"}}
    process_rule = {
        "mode": "automatic",  # 自动处理模式
        "rules": {
            "pre_processing_rules": [
                {"id": "remove_extra_spaces", "enabled": True},
                {"id": "remove_urls_emails", "enabled": True}
            ],
            "segmentation": {
                "separator": "\n",  # 分段分隔符
                "max_tokens": 1000  # 每段最大token数
            }
        }
    }
    # 使用纯文件名，避免路径中的 / 等字符导致 Dify 报 "Filename contains invalid characters"
    data = {}
    #try:
    #    import http.client as http_client
    #except ImportError:
    #    # Python 2
    #    import httplib as http_client
    #http_client.HTTPConnection.debuglevel = 1
    #logging.basicConfig()
    #logging.getLogger().setLevel(logging.DEBUG)
    #requests_log = logging.getLogger("requests.packages.urllib3")
    #requests_log.setLevel(logging.DEBUG)
    #requests_log.propagate = True
    data["indexing_technique"] = 'high_quality'
    data["process_rule"] = process_rule

    mydata = {}
    mydata['data'] = json.dumps(data)
    session = requests.Session()
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = session.post(url, headers=headers, files=files, data=mydata)
        logger.info(response.text)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logger.error("HTTP错误发生: %s", err)
        logger.error("响应内容: %s", err.response.text)
    return None

def query_datasets():
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
    }
    url = f"{DIFY_BASE_URL}/datasets"
    response = requests.get(url, headers=headers)
    logger.info("%s", response.json())

def get_docs_files() -> list:
    """
    Get all files in the specified directory and its subdirectories.

    This function searches for files with specified extensions in the
    directory specified by `configs.DOC_DIR` and its subdirectories.

    Returns:
        list: A list of file paths.

    Raises:
        ValueError: If the specified directory does not exist.
    """
    if not os.path.exists(DOC_DIR):
        raise ValueError(f"文档目录DOC_DIR（{DOC_DIR}）不存在")
    
    all_files = []
    
    for ext in DOC_SUFFIX.split(','):
        # 使用递归通配符 ** 搜索子目录中的文件
        files = glob.glob(f'{DOC_DIR}/**/*.{ext.strip()}', recursive=True)
        all_files.extend(files)

    return all_files 

if __name__ == '__main__':
    _setup_logging()
    try:
        file_list = get_docs_files()
        logger.info("共找到 %d 个文件，开始上传…", len(file_list))
        for i, path in enumerate(file_list):
            if i > 0 and i % 50 == 0:
                logger.info("已上传 50 个文件，休息 1 分钟…")
                time.sleep(60)
            logger.info("上传 (%d/%d): %s", i + 1, len(file_list), path)
            upload_doc(path)
    except ValueError as e:
        logger.error("%s", e)
    # query_datasets()