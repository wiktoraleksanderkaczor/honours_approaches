from flickr_download import download_from_flickr
from duckduckgo_download import download_from_ddg
from grayscale import grayscale
from check_similarity import compute_img_hashes, compute_hash_distances, \
    get_duplicate_images, delete_duplicates, feature_extraction, match_features, \
    total_matches, get_average_threshold, get_threshold_items, move_threshold_items

if __name__ == "__main__":
    # Define task
    image_folder = "dataset_builder/img_data/images"  # Source Folder
    gray_images = "dataset_builder/img_data/images_gray"  # Destination Folder
    hash_file_path = "./dataset_builder/hashes.p"
    img_dist_path = "./dataset_builder/imgs_d.p"
    compare_folder = "./dataset_builder/img_data/compare_set"
    compare_computed_data = "./dataset_builder/orb_data/orb_compare"
    img_computed_data = "./dataset_builder/orb_data/orb_images"
    consider_folder = "./dataset_builder/consider"
    num_images = 5000
    topic = "eiffel tower"

    # Download
    download_from_flickr(topic, num_images, image_folder)
    download_from_ddg(topic, image_folder)

    # Preprocessing
    max_resolution = grayscale(image_folder, gray_images)

    # Processing
    compute_img_hashes(gray_images, hash_file_path)
    compute_hash_distances(img_dist_path, hash_file_path)

    total_dup = get_duplicate_images(img_dist_path, threshold=10)
    print("There are", len(total_dup), "total duplicate images.")
    delete_duplicates(total_dup)

    feature_extraction(gray_images, compare_folder, img_computed_data,
                       compare_computed_data, points_num=8192)
    matches = match_features(
        img_computed_data, compare_computed_data, do_print=False)

    total = total_matches(matches, do_print=False)
    thr = get_average_threshold(totals, do_print=False):
    thr_total = get_threshold_items(totals, thr, max_resolution, do_print=False):
    move_threshold_items(totals, consider_folder, do_print=False)