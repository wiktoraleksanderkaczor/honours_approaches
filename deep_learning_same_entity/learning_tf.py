import os
import sys
import tensorflow as tf
import numpy as np
import glob
from random import randint as random
from random import choice as choice
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

#print(tf.__version__)

if __name__ == "__main__":
    RESUME = False
    print(sys.argv)
    print('Number of arguments:', len(sys.argv), 'arguments.')
    if len(sys.argv) == 1:
        print("No provided model checkpoint directory, not resuming training, starting from scratch.")
        print("The checkpoint directory will be in \"saved_model\".")
        if input("Do you wish to continue? (\"y\" or \"n\"): ") == "n":
            exit()
    else:
        print("Checkpoint resume directory provided, new checkpoints might overwrite the checkpoint in the directory.")
        if input("Do you wish to continue? (\"y\" or \"n\"): ") == "n":
            exit()
        RESUME = bool(sys.argv[1])
    
    physical_devices = tf.config.experimental.list_physical_devices('GPU')
    assert len(physical_devices) > 0, "Not enough GPU hardware devices available"
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
    # tf.config.experimental.set_virtual_device_configuration(physical_devices[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=5926)])

    batch_size = 16
    img_height = 224
    img_width = 224
    AUTOTUNE = tf.data.experimental.AUTOTUNE

    # Enable mixed precision training
    #os.environ["TF_ENABLE_AUTO_MIXED_PRECISION"] = "1"
    
    
    # Data directories
    train_files = glob.glob("/media/badfox/Data/tf_data/train/**/*.jpg", recursive=True)
    val_files = glob.glob("/media/badfox/Data/tf_data/val/**/*.jpg", recursive=True)
    train_ds, val_ds = [], []
    train_files, val_files = train_files[:-1], val_files[:-1]

    # Choose either the previous file in unshuffled set, or a random one from the set to add to list of tuples.
    for i in range(1, len(train_files), 2):
        if random(0,1) == 1:
            train_ds.append((train_files[i], train_files[i-1]))
        else:
            train_ds.append((train_files[i], choice(train_files)))

    for i in range(1, len(val_files), 2):
        if random(0,1) == 1:
            val_ds.append((val_files[i], val_files[i-1]))
        else:
            val_ds.append((val_files[i], choice(val_files)))
    
    
    train_ds = tf.data.Dataset.from_tensor_slices(train_ds)
    val_ds = tf.data.Dataset.from_tensor_slices(val_ds)

    print("Length of each dataset: ")
    train_len = tf.data.experimental.cardinality(train_ds).numpy()
    val_len = tf.data.experimental.cardinality(val_ds).numpy()
    print("Train: ", train_len)
    print("Validation: ", val_len)

    def get_label(file_paths):
        # convert the path to a list of path components
        parts1 = tf.strings.split(file_paths[0], os.path.sep)
        parts2 = tf.strings.split(file_paths[1], os.path.sep)
        # The second to last is the class-directory
        one_hot = parts1[-2] == parts2[-2]
        # THIS MIGHT BE SOMETHING TO COME BACK TO, IDK.
        one_hot = tf.cast(one_hot, tf.bool)
        
    
        # Integer encode the label
        #return tf.argmax(one_hot)
    
        return one_hot

    def decode_img(img):
        # convert the compressed string to a 3D uint8 tensor
        img = tf.image.decode_jpeg(img, channels=3)
        img = tf.image.resize(img, [img_height, img_width])
        #img = tf.image.convert_image_dtype(img, tf.float32)
        img = tf.keras.applications.resnet_v2.preprocess_input(img)
        # resize the image to the desired size
        return tf.cast(img, tf.float16)

    def process_path(file_paths):
        label = get_label(file_paths)
        # load the raw data from the file as a string
        img1 = tf.io.read_file(file_paths[0])
        img2 = tf.io.read_file(file_paths[1])
        img1 = decode_img(img1)
        img2 = decode_img(img2)
        return (img1, img2), label 

    # Shuffle the dataset and set `num_parallel_calls` so multiple images are loaded/processed in parallel.
    train_ds = train_ds.shuffle(train_len, reshuffle_each_iteration=False).map(process_path, num_parallel_calls=AUTOTUNE).cache("train_cache").shuffle(batch_size*2).batch(batch_size).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.shuffle(val_len, reshuffle_each_iteration=False).map(process_path, num_parallel_calls=AUTOTUNE).cache("val_cache").batch(batch_size).prefetch(buffer_size=AUTOTUNE)

    # Include the epoch in the file name (uses `str.format`)
    checkpoint_path = "saved_model/cp_epoch_{epoch:04d}.ckpt"
    checkpoint_dir = os.path.dirname(checkpoint_path)

    # Create a callback that saves the model's weights every 1 epochs
    cp_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_path,
        verbose=1,
        save_weights_only=True,
        save_freq="epoch")

    input1 = tf.keras.Input(shape=(224, 224, 3))
    input2 = tf.keras.Input(shape=(224, 224, 3))
    resnet = (tf.keras.applications.ResNet50V2(
        include_top=False, weights="imagenet", input_tensor=None, 
        input_shape=(224, 224, 3), pooling="avg"
    ))
    #resnet.trainable = False
    o1 = resnet(input1)
    o2 = resnet(input2)
    o3 = tf.keras.layers.Concatenate()([o1,o2])
    dense1 = tf.keras.layers.Dense(500, activation="relu", name="fc500")(o3)
    dense2 = tf.keras.layers.Dense(1, activation="relu", name="fc1")(dense1)
    model = tf.keras.Model(inputs=(input1, input2), outputs=dense2, name="same_entity")

    # AMP training
    # The original default learning rate is 0.001
    opt = tf.keras.optimizers.Adam()
    #opt = tf.keras.optimizers.Adam(learning_rate=0.01)
    #opt = tf.train.experimental.enable_mixed_precision_graph_rewrite(opt)

    model.compile(
        optimizer=opt,
        loss=tf.losses.CategoricalCrossentropy(from_logits=True),
        metrics=['accuracy'])

    if not RESUME:
        model.summary()

        # Save the weights using the `checkpoint_path` format
        model.save_weights(checkpoint_path.format(epoch=0))

        # Iterate over dataset.
        """
        #count = 0
        for e in train_ds:
            exec("")
            #print(e)
            #count = count + 1
            #print(count)
            #next(train_ds)
        """

        # Train model.
        model.fit(train_ds, epochs = 50, batch_size = batch_size, validation_data=val_ds, callbacks=[cp_callback])

    else:
        # Figure out the latest model saved
        latest = tf.train.latest_checkpoint(checkpoint_dir)
        
        # Figure out the latest epoch from the filename.
        print("Latest model: ", latest)
        latest_epoch = latest.split("_")[-1]
        latest_epoch = latest_epoch.split(".")[-2]
        latest_epoch = int(latest_epoch)
        print(latest_epoch)

        # Load the previously saved weights
        model.load_weights(latest)

        # Re-evaluate the model
        #loss, acc = model.evaluate(val_ds, verbose=2)
        #print("Restored model, accuracy: {:5.2f}%".format(100*acc))

        # Train model.
        model.fit(train_ds, epochs = 50, initial_epoch=latest_epoch, batch_size = batch_size, validation_data=val_ds, callbacks=[cp_callback])
