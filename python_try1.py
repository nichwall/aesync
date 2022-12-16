from fuzzysearch import find_near_matches_in_file, find_near_matches
import subprocess
import time
import csv
from random import randint

def extract_snippet(fname, start, duration=10):
    # Extract to a temp file
    temp_filename = f"work/seg_{start}.wav"
    cmd = f"""ffmpeg -y -loglevel panic -ss {start} -to {start+duration} -i "{fname}" "{temp_filename}" """
    
    # Run command
    subprocess.run(cmd, shell=True)

    # Transcribe audio
    cmd = f"spchcat {temp_filename}"
    ret_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

    return ret_output

def get_position(search_str):
    max_l_dist = 5
    max_max = 10
    nearest = []
    while len(nearest) == 0 and max_l_dist <= max_max:
        with open("work/input.txt", 'r') as f:
            try:
                nearest = find_near_matches_in_file(search_str, f, max_l_dist=max_l_dist)
            except:
                nearest = []
                break
            if len(nearest) == 0:
                print("Didn't find anything, trying again...")
                max_l_dist += 5
    return nearest

def fancy_get_position(fname, start, duration=10, debug=False):
    if debug:
        print()
        print("Extracting audio...")

    # Extract the snippet
    search_str = extract_snippet(fname, start, duration=duration)

    # Figure out percentage of audiobook position
    audiobook_percentage = start / get_audio_length(fname)
    # Once we have this percentage, subtract 3% for searching in text
    audiobook_percentage -= 0.05
    if audiobook_percentage < 0:
        audiobook_percentage = 0

    if debug:
        print("Trimming text...")
    # Use percentage to get starting point of where to look
    with open("work/input.txt",'r') as f:
        fsize = len(f.read())

    text_start_loc = int( audiobook_percentage       * fsize)
    text_end_loc   = int((audiobook_percentage+0.1) * fsize)
    if text_end_loc > fsize:
        text_end_loc = fsize

    if debug:
        print(f"Text start location: {text_start_loc}    percent: {audiobook_percentage}")
        print(f"Text end location  : {text_end_loc}    percent: {audiobook_percentage+0.1}")

    with open("work/input.txt", 'r') as f:
        text_search = f.read()[text_start_loc:text_end_loc]

    # Look for search string in subsection
    if debug:
        print("Searching...")
    try:
        nearest = find_near_matches(search_str, text_search, max_l_dist=7)
        # Adjust start position by actual start position
        return nearest[0].start + text_start_loc
    except:
        return -1

def convert_ebook(fname):
    # Convert epub to txt using epub2txt2
    cmd = f"""./epub2txt2/epub2txt "{fname}" > work/input.txt"""
    subprocess.run(cmd, shell=True)

    fsize = 0
    with open("work/input.txt",'r') as f:
        fsize = len(f.read())

    return fsize

def get_audio_length(fname):
    cmd = f"""ffprobe -i "{fname}" -show_format -v quiet | sed -n 's/duration=//p'"""
    ret_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.split()[-1]

    return float(ret_output)

def random_sample(fname, mapping, audiobook_length, duration=10):
    ebook_actual = -1
    while (ebook_actual < 0):
        # Gets random sample from the book and calculate error
        sample_time = randint(1, int(audiobook_length))
        ebook_actual = fancy_get_position(fname, sample_time, duration=duration)

    # Estimate position in book
    ebook_guess = get_position_by_time(mapping, sample_time)

    # Get the error
    #print(f" Random sample occurring at {sample_time} seconds:  Guess = {ebook_guess}  Actual = {ebook_actual}    error: {ebook_actual - ebook_guess}")
    print(f" Random sample occurring at {sample_time} seconds error: {int(ebook_actual - ebook_guess)} characters")


def get_position_by_time(mapping, sample_time):
    times = []
    positions = []
    for entry in mapping:
        times.append(int(entry["time"]))
        positions.append(int(entry["position"]))

    #interped = interp1d(times, positions)
    #return interped(sample_time)

    # Own interpolation to see if it's better
    
    # Find closest lower
    idx = 0
    #print(f"Sample time: {sample_time}")
    #print(f"Mapping: {mapping}")
    while times[idx] < sample_time:
        #print(f"  idx: {idx} / {len(times)}")
        idx += 1

    lowest = idx
    highest = idx + 1

    # Check if out of bounds
    if highest > len(times):
        lowest  -= 1
        highest -= 1

    x1 = times[lowest ]
    x2 = times[highest]
    y1 = positions[lowest ]
    y2 = positions[highest]

    position = y1 + (sample_time - x1)*(y2-y1)/(x2-x1)

    #print(f" time bounds: {times[lowest]}  ->  {times[highest]}")

    return position




BOOK_NAME = "Oathbringer"
#BOOK_NAME = "Sufficiently Advanced Magic"

# Set up EPUB
fsize = convert_ebook(f"{BOOK_NAME}.epub")

# Get length of audio file
audio_length = get_audio_length(f"{BOOK_NAME}.m4a")

# Get time stamps

"""
time_map = []
#for start in range(100, int(audio_length), 300):
for start in range(100, int(audio_length), 900):
#for start in range(100, int(audio_length), 2000):
    position = fancy_get_position(f"{BOOK_NAME}.m4a", start, duration=4)
    if position < 0:
        continue
    print(f"  Actual location found: {position}")

    percent = position / fsize * 100

    # Add to lookup
    mapper = {"time": start, "percentage": percent, "position": position}
    time_map.append(mapper)

    #print(position)
    print(f"Percentage of book: {percent}")
    print()

with open('test.csv','w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=time_map[0].keys())
    writer.writeheader()
    writer.writerows(time_map)
    """

time_map = []
with open('test.csv','r') as csvfile:
    reader = csv.DictReader(csvfile)
    for line in reader:
        time_map.append(line)


for i in range(10):
    random_sample(f"{BOOK_NAME}.m4a", time_map, audio_length, duration=4)
