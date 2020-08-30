from PIL import Image
import glob
import imagehash
from tqdm import tqdm
import random
from pprint import pprint
import concurrent.futures
import multiprocessing


WORKERS = 8

# Function to split list into chunks.
def chunks(lst, n):
    # Yield successive n-sized chunks from lst.
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def Sort(sub_li):
	l = len(sub_li)
	for i in range(0, l):
		for j in range(0, l-i-1):
			if (sub_li[j][1] > sub_li[j + 1][1]):
				tempo = sub_li[j]
				sub_li[j]= sub_li[j + 1]
				sub_li[j + 1]= tempo
	return sub_li

def thread_hash(chunk, hash0, tmp_calc):
	for i in chunk:
		hash1 = imagehash.average_hash(Image.open(i))
		tmp_calc.append(hash0 - hash1)

def check_stats(directory):
	files = glob.glob(directory+"/*.jpg")
	files_calc = []
	shuffle_num = 5

	for i in tqdm(files):
		tmp_calc = []
		hash0 = imagehash.average_hash(Image.open(i))
        
		chunks_list = chunks(random.sample(files, shuffle_num), WORKERS)        
		for chunk in chunks_list:
			with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
				executor.submit(thread_hash, chunk, hash0, tmp_calc)
		del(chunks_list)

		count = 0
		for k in tmp_calc:
			count += k
		#count = count / len(tmp_calc)
		count = count / shuffle_num
		files_calc.append([i, count])

	mini = 1000
	maxi = 0
	for i in files_calc:
		if mini > i[1]:
			mini = i[1]
		if maxi < i[1]:
			maxi = i[1]

	#pprint(Sort(files_calc))
	print("dir:", directory, " min: ", mini, ", max: ", maxi, " variance: ", maxi-mini)
	return [directory, mini, maxi, maxi-mini]
