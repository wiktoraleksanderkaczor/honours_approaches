import glob, json
files = glob.glob("matches/*")
total = 0
for fi in files:
    data = json.load(open(fi))
    total += data["wall_time"]

print("TOTAL:", total)
print("TOTAL_AVG:", total / len(files))

