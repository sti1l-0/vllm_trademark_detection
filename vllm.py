import base64
import json
import requests
import yaml
import sys


from loguru import logger
from queue import Queue
from threading import Thread

logger.remove()
logger.add(sys.stderr, level="ERROR")


class bot:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)

    def load_config(self, filename: str) -> dict:
        with open(filename, "r") as f:
            config = yaml.load(stream=f.read(), Loader=yaml.FullLoader)
        logger.debug(config["vllm"])
        return config["vllm"]

    def bot_chat(self, user_content: list | str):
        messages = [
            {
                "role": "system",
                "content": "你是一名广告专家，为了在设计广告时需正确运用品牌标志，你几乎了解市面上所有的品牌标志，无论是汽车车标、各种品牌logo、以及具有特点的品牌元素你全都能认出来。",
            },
            {"role": "user", "content": user_content},
        ]
        data = json.dumps({"model": self.config.get("model"), "messages": messages})

        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.get('auth')}",
        }
        resp = requests.post(self.config.get("addr"), headers=header, data=data)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"请求响应错误，状态码：{resp.status_code}\n{resp.text}")
            raise ValueError("请求错误")

    def b64_encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            image_data = f.read()
            encoded_image = base64.b64encode(image_data)
        return encoded_image.decode("utf-8")

    def trademark_detect(self, image_path: str):
        b64image = self.b64_encode_image(image_path)
        image_request_content = [
            {"type": "image_url", "image_url": {"url": b64image}},
            {
                "type": "text",
                "text": "请你仔细观察这张图片，识别其中存在的所有品牌元素，并告诉我与之对应的品牌名称",
            },
        ]
        resp = self.bot_chat(image_request_content)

        logger.debug(resp)

        return resp

    def conclude(self, dirt: str):
        build_dirt = "\n".join([i for i in dirt])
        logger.debug(build_dirt)
        _ = self.bot_chat(
            f"请你统计这段文字中总共出现了哪些知名的品牌,将这些品牌出现的次数由高到低排列后告诉我：\n{build_dirt}"
        )
        logger.debug(_)
        return _


class ThreadPool:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.num_threads = self.config.get("threads")
        self.task_queue = Queue()
        self.results = []
        self.threads = [Thread(target=self.worker) for _ in range(self.num_threads)]
        for thread in self.threads:
            thread.start()

    def load_config(self, filename: str) -> dict:
        with open(filename, "r") as f:
            config = yaml.load(stream=f.read(), Loader=yaml.FullLoader)
        logger.debug(config["concurrency"])
        return config["concurrency"]

    def worker(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            func, args = task
            result = func(*args)
            self.results.append(result)
            self.task_queue.task_done()

    def add_task(self, func, args):
        self.task_queue.put((func, args))

    def close(self):
        for _ in range(self.num_threads):
            self.task_queue.put(None)
        for thread in self.threads:
            thread.join()

    def get_results(self):
        return self.results


if __name__ == "__main__":
    #
    # vbot = bot("./config.yml")
    # print(vbot.trademark_detect("./image.jpg"))
    #
    vbot = bot("./config.yml")
    pool = ThreadPool("./config.yml")
    for _ in range(2):
        pool.add_task(func=vbot.trademark_detect, args=("./image.jpg",))
    pool.close()
    results = pool.get_results()

    logger.debug(results)

    conclusion = vbot.conclude(results)
    print(conclusion)
