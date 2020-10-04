import os
import glob
import shutil
import pandas
import pickle
import concurrent.futures
import multiprocessing

WORKERS = multiprocessing.cpu_count()

# SECTION: GENERATE AND WRITE "image_files" DATA FROM FILESYSTEM.
def gen_glob_path_for(name):
    DATA_DIR = name + "**/*.jpg"
    # Retrieve all *.jpg files in the dataset.
    image_files = glob.glob(DATA_DIR, recursive = True)
    print("FINISHED READING FILESYSTEM FOR ALL JPGs in: " + DATA_DIR)
    return image_files


# Function to split list into chunks.
def chunks(lst, n):
    # Yield successive n-sized chunks from lst.
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# Function to run on each thread for mapping filenames to landmarks.
def thread_id_to_path(chunk, image_and_landmark, id_to_path):
    counter = 0
    chunk_len = len(chunk)
    for path in chunk:
        # Get the filename.
        filename = path.split("/")[-1]
        try:
            # See if it exists in the mapping, get landmark ID, if not, throw error and inform.
            the_key = image_and_landmark[filename]

            #Check if landmark ID already exist in the dictionary.
            if the_key in id_to_path:
                # If so, append the path to the list under said key.
                id_to_path[the_key].append(path)
            else:
                # Else create a list containing the path at the key.
                id_to_path[the_key] = [path]
        # If key doesn't exist print filename.
        except KeyError:
            print("Can't find " + filename)
        # Print progress every N items.
        counter += 1
        if counter % (chunk_len//100) == 0:
            print(str(counter) + "/" + str(chunk_len), str((100/chunk_len)*counter) + "%")


def create_all_dirs_train(id_and_path, dst):
    # Setup total dirs to make var, problems storing list, and progress counter.
    total, problems, counter = len(id_and_path), [], 0
    # For landID mapped to path.
    for item in id_and_path.keys():
        # Path to create to store data to be moved.
        new_path = dst + str(item) + "/"

        # Create containing directory if it doesn't exist.
        if not os.path.isdir(new_path):
            try:
                os.makedirs(new_path)
            except Exception as e:
                # If anything fails, add to problems list.
                problems.append((e, new_path))

        # Show progress
        counter += 1
        if counter % (total//100) == 0:
            print(str(counter) + "/" + str(total), str((100/total)*counter) + "%")
    
    # Write out problems list for debugging.
    print(len(problems), " problems occured, list writted to: ./pickles/problems_create_dirs_train.pickle")
    with open("./pickles/problems_create_dirs_train.pickle", "wb+") as f:
        pickle.dump(problems, f)


def copy_all_files(id_and_path, dst):
    # Setup total files to copy var, problems storing list, and progress counter.
    total, problems, counter = len(id_and_path), [], 0
    # For each landID mapped to path.
    for item in id_and_path.keys():
        # Path to create to store data to be copied.
        new_path = dst + str(item) + "/"
        for path in id_and_path[item]:
            # Copy the file.
            try:
                shutil.copy(path, new_path)
            except Exception as e:
                # If anything fails, add to problems list.
                problems.append((e, (item, path)))

        # Show progress
        counter += 1
        if counter % (total//100) == 0:
            print(str(counter) + "/" + str(total), str((100/total)*counter) + "%")
    
    # Write out problems list for debugging.
    print(len(problems), " problems occured, list writted to: ./pickles/problems_copy_files_train.pickle")
    with open("./pickles/problems_copy_files_train.pickle", "wb+") as f:
        pickle.dump(problems, f)

if __name__ == "__main__":
    # Read CSV to get image names for each landmark_id.
    data = pandas.read_csv("./CSVs/train/train.csv")
    print("FINISHED READING CSV FILE")

    # Prepare Dict to store data and get number of rows in CSV.
    img_and_landID_train, len_data = {}, len(data["id"])
    
    # For each row in CSV.
    for i in range(len_data):
        # Map image name to landID in dictionary
        img_and_landID_train[str(data["id"][i])+".jpg"] = data["landmark_id"][i]
        # Print progress every N rows.
        if i % 10000 == 0:
            print(i,"/",len_data,"{:.2f}%".format((100/len_data)*i))
    print("FINISHED IMPORTING TO DICT: " + str(len(img_and_landID_train)) + " items")

    # Delete read CSV to save memory.
    del(data)
    
    # Generate list of all .jpg file paths in "train" folder in "extracted_data".
    image_files_in_train = gen_glob_path_for("../../train/")

    # Write out the above to save time for later reading.
    with open("./pickles/image_files_in_train.pickle", "wb+") as f:
        pickle.dump(image_files_in_train, f)

    # Go through the dictionary (mapping filename to landID) and filepaths, match them up, multi-threaded.
    id_to_path_train = {}
    chunks_list = chunks(image_files_in_train, WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            executor.submit(thread_id_to_path, chunk, img_and_landID_train, id_to_path_train)
    del(chunks_list)

    with open("./pickles/id_to_path_train.pickle", "wb+") as f:
        pickle.dump(id_to_path_train, f)

    with open("./pickles/img_and_landID_train.pickle", "wb+") as f:
        pickle.dump(img_and_landID_train, f)
    
    # Save memory.
    del(image_files_in_train)
    del(img_and_landID_train)

    # NOW, I HAVE TO FIND THE MOST IMAGE CONTAINING CLASSES.
    num_classes, count = 500, 0
    biggest_classes = {}
    for k in sorted(id_to_path_train, key=lambda k: len(id_to_path_train[k]), reverse=True):
        biggest_classes[k] = id_to_path_train[k]
        count += 1
        if count == num_classes:
            break
    
    # Save memory.
    del(id_to_path_train)

    # Get only up to "N" images per class.
    upto_limit = 500
    for key in biggest_classes.keys():
        if len(biggest_classes[key]) > upto_limit:
            biggest_classes[key] = biggest_classes[key][:upto_limit]

    # Create folders for each landmarkid in "../torch_data/train", sort copy images 
    # from ../extracted_data/train, sort into landmarkid and put in ../torch_data 
    create_all_dirs_train(biggest_classes, "../tf_data/train/")
    copy_all_files(biggest_classes, "../tf_data/train/")
