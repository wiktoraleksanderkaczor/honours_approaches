from flickr_download import download_from_flickr
from duckduckgo_download import download_from_ddg
from grayscale import grayscale
from check_similarity import compute_img_hashes, compute_hash_distance, \
    get_duplicate_images, delete_duplicates, feature_extraction, match_features, \
    total_matches, get_average_threshold, get_threshold_items, move_threshold_items, \
    get_matcher, match_features_compare, get_compare_threshold_items

def runner():
    # Define task
    compare_set = "dataset_builder/img_data/compare_set"
    image_folder = "dataset_builder/img_data/images"  # Source Folder
    gray_images = "dataset_builder/img_data/images_gray"  # Destination Folder
    blurry_folder = "dataset_builder/img_data/images_blurry"
    small_folder = "dataset_builder/img_data/images_small"
    hash_file_path = "./dataset_builder/hashes.p"
    img_dist_path = "./dataset_builder/imgs_d.p"
    compare_folder = "./dataset_builder/img_data/compare_set_gray"
    compare_computed_data = "./dataset_builder/pts_data/compare"
    img_computed_data = "./dataset_builder/pts_data/images"
    consider_folder = "./dataset_builder/consider"
    compute_cache = "./dataset_builder/compute_cache.mpts"
    thr_compute_cache = "./dataset_builder/thr_compute_cache.mpts"
    num_images = 15000
    compare_img_num = 100
    topic = "eiffel tower"

    # Download comparison set
    #download_from_ddg(topic, compare_set)
    # compare_img_num

    # Preprocess comparison set.
    # No need to capture max_resolution.
    compare_max_res, ref_blur, _ = grayscale(compare_set, compare_folder, small_folder, blurry_folder)
    #input("You can check your comparison set now... Then, enter any key.")

    # Download image set
    #download_from_flickr(topic, num_images, image_folder)

    # Removing duplicates
    print("Computing image hashes:")
    compute_img_hashes(image_folder, hash_file_path)
    print("Computing hash distances:")
    compute_hash_distance(image_folder, img_dist_path, hash_file_path)

    print("Finding duplicate images:")
    total_dup = get_duplicate_images(img_dist_path, threshold=10)
    print("There are", len(total_dup), "total duplicate images.")
    delete_duplicates(total_dup)

    # Preprocessing image set
    max_resolution, _, avg_res = grayscale(image_folder, gray_images, small_folder, blurry_folder, ref_blur=ref_blur, do_print=True)

    feature_extraction(gray_images, compare_folder, img_computed_data,
                       compare_computed_data, feature_matcher="ORB", points_num=4096)

    # Create matcher
    matcher = get_matcher(feature_matcher="ORB", bf_or_flann="BF")

    # Compare set threshold
    matches = match_features_compare(compare_computed_data, thr_compute_cache, matcher, ratio_test=True, do_print=False)
    totals = total_matches(matches, do_print=False)
    thr = get_average_threshold(totals, do_print=False)
    # Does Lowe ratio apply here?
    #thr = thr*0.75

    over_thr = get_compare_threshold_items(totals, thr, compare_max_res, compare_folder, get_scaled_thr_only=True)
    thr = get_average_threshold(over_thr)


    # Match the image data.
    matches = match_features(
        img_computed_data, compare_computed_data, compute_cache, matcher, ratio_test=True, do_print=False)
    
    # Get the totals for image data.
    totals = total_matches(matches, do_print=False)

    # Get all items under threshold
    # 0.99900 is from COLMAP default for feature matching.
    conf = 0.99850
    below_thr = get_threshold_items(totals, gray_images, thr, max_resolution, show=True)
    #below_thr, over_thr = get_threshold_items(totals, thr, avg_res, gray_images, do_print=True)


    # Move all items under threshold
    move_threshold_items(below_thr, consider_folder, do_print=False)

if __name__ == "__main__":
    runner()