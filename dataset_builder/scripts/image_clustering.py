import os
import glob
import numpy as np
from tqdm import tqdm
from shutil import copyfile, rmtree
from concurrent.futures import ThreadPoolExecutor


from sklearn.cluster import KMeans

def create_cluster_folders(n_clusters, path="output/"):
    rmtree(path)
    os.mkdir(path)
    for i in range(n_clusters):
        os.mkdir(path+str(i))

def cluster(data_dir, n_clusters):
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications import InceptionResNetV2
    from tensorflow.keras.applications.inception_resnet_v2 import preprocess_input

    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    model = InceptionResNetV2(weights='imagenet', include_top=False)
    model.summary()

    print("Getting features...")
    feature_list = []
    images = glob.glob("{}*".format(data_dir))
    for img_path in tqdm(images):
        img = image.load_img(img_path, target_size=(224, 224))
        img_data = image.img_to_array(img)
        img_data = np.expand_dims(img_data, axis=0)
        img_data = preprocess_input(img_data)
        feature = model.predict(img_data)
        feature_np = np.array(feature)
        feature_list.append(feature_np.flatten())

    print("Training K-Means clustering...")
    feature_list_np = np.array(feature_list)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(feature_list_np)

    print("Copying files to respective clusters...")
    for item in tqdm(zip(images, feature_list)):
        img_path, feature = item
        pred = kmeans.predict(feature.reshape(1, -1))[0]
        fname = img_path.split("/")[-1]
        copyfile(img_path, "output/"+str(pred)+"/"+fname)

    print("Clearing session...")
    tf.keras.backend.clear_session()