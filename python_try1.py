from fuzzysearch import find_near_matches_in_file
import subprocess
import time

def extract_snippet(fname, start, duration=10):
    # Extract to a temp file
    temp_filename = f"segments/seg_{start}.wav"
    cmd = f"""ffmpeg -loglevel panic -i "{fname}" -ss {start} -to {start+duration} "{temp_filename}" """
    
    # Run command
    subprocess.run(cmd, shell=True)

    # Transcribe audio
    cmd = f"spchcat {temp_filename}"
    ret_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

    return ret_output

def get_position(fname, search_str):
    max_l_dist = 20
    max_max = 35
    nearest = []
    while len(nearest) == 0 and max_l_dist <= max_max:
        with open(fname, 'r') as f:
            nearest = find_near_matches_in_file(search_str, f, max_l_dist=max_l_dist)
            if len(nearest) == 0:
                print("Didn't find anything, trying again...")
                max_l_dist += 5
                time.sleep(2)
    return nearest

#transcription = extract_snippet("input.m4a", 4100)
#position = get_position("input.txt", transcription)
#print(position)
for start in range(100, 10000, 1000):
    transcription = extract_snippet("input.m4a", start)
    position = get_position("input.txt", transcription)
    print(position)
