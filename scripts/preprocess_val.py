import os 
import glob
import shutil
import pickle

# SECTION: GENERATE AND WRITE "image_files" DATA FROM FILESYSTEM.
def gen_glob_path_for(name):
    DATA_DIR = name + "**/*.jpg"
    # Retrieve all *.jpg files in the dataset.
    image_files = glob.glob(DATA_DIR, recursive = True)
    print("FINISHED READING FILESYSTEM FOR ALL JPGs in: " + DATA_DIR)
    return image_files

def create_all_dirs_val(id_and_path, dst):
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
    print(len(problems), " problems occured, list writted to: ./pickles/problems_create_dirs_val.pickle")
    with open("./pickles/problems_create_dirs_val.pickle", "wb+") as f:
        pickle.dump(problems, f)

def move_all_files(id_and_path, dst):
    # Setup total files to copy var, problems storing list, and progress counter.
    total, problems, counter = len(id_and_path), [], 0
    # For each landID mapped to path.
    for item in id_and_path.keys():
        # Path to create to store data to be copied.
        new_path = dst + str(item) + "/"
        for path in id_and_path[item]:
            # Copy the file.
            try:
                shutil.move(path, new_path)
            except Exception as e:
                # If anything fails, add to problems list.
                problems.append((e, (item, path)))

        # Show progress
        counter += 1
        if counter % (total//100) == 0:
            print(str(counter) + "/" + str(total), str((100/total)*counter) + "%")
    
    # Write out problems list for debugging.
    print(len(problems), " problems occured, list writted to: ./pickles/problems_move_files_val.pickle")
    with open("./pickles/problems_move_files_val.pickle", "wb+") as f:
        pickle.dump(problems, f)

if __name__ == "__main__":
    train_paths = gen_glob_path_for("../tf_data/train/")

    folders = {}
    for item in train_paths:
        key = item.split("/")[-2]
        if key not in folders:
            folders[key] = [item]
        else:
            folders[key].append(item)

    #print(folders)
    print(len(folders))
    
    val_data = {}
    for key in folders.keys():
        to_take = (len(folders[key]) // 100) * 20 # 20%
        val_data[key] = folders[key][:to_take]
        print(val_data[key])

    create_all_dirs_val(val_data, "../tf_data/val/")
    move_all_files(val_data, "../tf_data/val/")
