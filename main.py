import os

import key_frame
import vllm


if __name__ == "__main__":
    video = "demo/pepsi_ad.mp4"
    frame_folder = key_frame.key_frame_image(video)
    images = os.listdir(frame_folder)

    bot = vllm.bot("./config.yml")
    pool = vllm.ThreadPool("./config.yml")
    for image in images:
        pool.add_task(func=bot.trademark_detect, args=(f"{frame_folder}/{image}",))
    pool.close()
    results = pool.get_results()

    conclusion = bot.conclude(results)
    print(conclusion)
