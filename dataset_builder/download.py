from flickr_download import download
from duckduckgo_download import download_from_ddg

if __name__ == "__main__":
    topic = "eiffel tower"
    download(topic, num_images=5000)
    download_from_ddg(topic)