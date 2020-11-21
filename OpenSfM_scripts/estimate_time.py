#!/home/badfox/miniconda3/bin/python
N = 300
T = 10

TOTAL = 0
for i in range(N):
    item = (T/N) * i
    TOTAL += item
    #print(item)
    # Slowly increasing to maximum time.

print("Total (S):", TOTAL)
print("Total (M):", TOTAL/60)
print("Total (H):", (TOTAL/60)/60)

#2020-10-24 05:09:06,363 INFO: Matched 1098903 pairs for 1483 ref_images (perspective-perspective: 1098903) in 9244.413207308 seconds (0.008412401467125852 seconds/pair).

