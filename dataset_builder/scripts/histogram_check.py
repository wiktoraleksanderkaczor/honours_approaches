from common import *

# MASSIVE WIP

histSize = 256
histRange = (0, 256) # the upper boundary i
accumulate = False

def histogram_thread(fi):
    try:
        image = cv2.imread(fi)
        bgr_planes = cv2.split(image)
        b_hist = cv2.calcHist(bgr_planes, [0], None, [histSize], histRange, accumulate=accumulate)
        g_hist = cv2.calcHist(bgr_planes, [1], None, [histSize], histRange, accumulate=accumulate)
        r_hist = cv2.calcHist(bgr_planes, [2], None, [histSize], histRange, accumulate=accumulate)
        new = []
        for b, g, r in zip(b_hist, g_hist, r_hist):
            total = b + g + r     
            new.append(total/3)

        num_differing = 0

        for b, g, r, total in zip(b_hist, g_hist, r_hist, new):
            b_per = b / total
            g_per = g / total
            r_per = r / total
            diff = False
            if b_per > 1.15 or b_per < 0.85:
                diff = True
            if g_per > 1.15 or g_per < 0.85:
                diff = True
            if r_per > 1.15 or r_per < 0.85:
                diff = True
            if diff:
                num_differing += 1
        
        return (fi, num_differing)


    except Exception as e:
        print(fi, e)

def check_histogram(data_dir):
    data_files = glob.glob(data_dir+"*.jpg")

    num_differing_data = thread_it_return(histogram_thread, data_files)

    # 200 seems to be a good constant
    data_to_move = []
    for fi, num_differing in num_differing_data:
        if num_differing < 200:
            data_to_move.append(fi)

    return data_to_move
