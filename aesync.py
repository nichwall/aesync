from fuzzysearch import find_near_matches_in_file, find_near_matches
import subprocess
import time
import csv
from random import randint

import tempfile
from os import path

import argparse

import whisper

def interp(x, x1, y1, x2, y2):
    return y1 + (x - x1)*(y2-y1)/(x2-x1)

class AESync:
    def __init__(self, fname_ebook, fname_audio, fname_map, model="tiny", max_l_dist=7):
        self.fname_map   = fname_map
        self.fname_ebook = fname_ebook
        self.fname_audio = fname_audio
        
        self.mapping = []

        self.model = whisper.load_model("tiny")

        self.max_l_dist = max_l_dist

        self.ebook_size   = 0
        self.audio_length = 0

        self.temp_dir = tempfile.gettempdir()

    def convert_ebook(self):
        # Get file format of ebook
        ebook_format = self.fname_ebook.split(".")[-1]

        input_txt = path.join(self.temp_dir, "input.txt")

        if ebook_format == "epub":
            # Convert epub to txt using epub2txt2
            cmd = f"""./epub2txt2/epub2txt "{self.fname_ebook}" > {input_txt}"""
        elif ebook_format == "txt":
            # Just copy the book if text file
            cmd = f"""cp "{self.fname_ebook}" {input_txt}"""

        subprocess.run(cmd, shell=True)

        with open(input_txt,'r') as f:
            self.ebook_size = len(f.read())

    def get_audio_length(self):
        # Get length of audio file in seconds
        cmd = f"""ffprobe -i "{self.fname_audio}" -show_format -v quiet | sed -n 's/duration=//p'"""
        ret_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.split()[-1]

        self.audio_length = float(ret_output)

    def extract_snippet(self, start, duration=10, debug=False):
        # Extract to a temp file
        temp_filename = path.join(self.temp_dir, f"seg.wav")
        cmd = f"""ffmpeg -y -loglevel panic -ss {start} -to {start+duration} -i "{self.fname_audio}" "{temp_filename}" """

        # Run command
        subprocess.run(cmd, shell=True)

        # Transcribe audio
        result = self.model.transcribe(temp_filename, fp16=False)
        if debug:
            print(f" Result: {result['text']}")

        return result["text"]

    def align_book(self, step_size=1000, duration=10):
        # Clear mapping if done
        self.mapping = []

        # Ensure ebook is converted
        if self.ebook_size == 0:
            self.convert_ebook()

        # Ensure we have the audio length
        if self.audio_length == 0:
            self.get_audio_length()

        # Iterate over the book and get snippets
        for start in range(100, int(self.audio_length)-duration, step_size):
            print(f" Aligning at {start} seconds")
            position = self.get_position(start, duration)
            if position < 0:
                continue

            percent = position / self.ebook_size * 100

            new_mapping = {"time": start, "percentage": percent, "position": position}
            self.mapping.append(new_mapping)

        # TODO Check if any large gaps need to be remapped?

    def get_position(self, start, duration, debug=False):
        # Extract the snippet
        search_str = self.extract_snippet(start, duration=duration, debug=debug)

        # Figure out percentage of audiobook position
        audiobook_percentage = start / self.audio_length
        # Once we have this percentage, subtract 3% for searching in text
        audiobook_percentage -= 0.02
        if audiobook_percentage < 0:
            audiobook_percentage = 0

        # Use percentage to get starting point of where to look
        text_start_loc = int( audiobook_percentage      * self.ebook_size)
        text_end_loc   = int((audiobook_percentage+0.04) * self.ebook_size)
        if text_end_loc > self.ebook_size:
            text_end_loc = self.ebook_size

        with open(path.join(self.temp_dir, "input.txt"), 'r') as f:
            text_search = f.read()[text_start_loc:text_end_loc]

        # Look for search string in subsection
        try:
            nearest = find_near_matches(search_str, text_search, max_l_dist=self.max_l_dist)
            # Adjust start position by actual start position
            return nearest[0].start + text_start_loc
        except:
            return -1

    def time2pos(self, audio_time):
        # Interpolate between points
        times = []
        positions = []
        for entry in self.mapping:
            times.append(int(entry["time"]))
            positions.append(int(entry["position"]))

        # Find closest lower
        idx = 0
        while idx < len(times) and times[idx] < audio_time:
            idx += 1

        lowest = idx
        highest = idx + 1

        # Check if out of bounds
        if highest >= len(times):
            lowest  -= 1
            highest -= 1

        position = interp( audio_time, \
                           times[lowest ], positions[lowest ], \
                           times[highest], positions[highest])
        return position

    def validate(self, count=10, error_thresh=500):
        # Select random points in the book to see how well
        # the mapping works. If book error is too high, add more points?

        for idx in range(count):
            ebook_actual = -1
            while (ebook_actual < 0):
                sample_time = randint(1, int(self.audio_length))
                ebook_actual = self.get_position(sample_time, duration=4, debug=True)

            # Estimate position in book
            ebook_guess = self.time2pos(sample_time)

            print(f"Random sample occurring at {sample_time} seconds error: {int(ebook_actual - ebook_guess)} characters")

    def store(self, method="csv"):
        with open(self.fname_map,'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.mapping[0].keys())
            writer.writeheader()
            writer.writerows(self.mapping)

    def load(self, method="csv"):
        # Ensure ebook is converted
        if self.ebook_size == 0:
            self.convert_ebook()

        # Ensure we have the audio length
        if self.audio_length == 0:
            self.get_audio_length()

        with open(self.fname_map,'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for line in reader:
                self.mapping.append(line)

if __name__ == "__main__":

    argParser = argparse.ArgumentParser()
    argParser.add_argument('audio_file')
    argParser.add_argument('ebook_file')
    argParser.add_argument('output_file')
    argParser.add_argument('-n', action='store_true', dest='no_generate', help='Load map file instead of aligning files.')
    argParser.add_argument('-c', '--count',      type=int, default=10, help='How many validation samples to run.')
    argParser.add_argument('-l', '--max_l_dist', type=int, default= 7, help='Max L distance for fuzzy string matching. Higher numbers are more likely to find a match but also take longer.')
    argParser.add_argument('-s', '--stepsize',   type=int, default=1000, help='Step size between samples in seconds.')
    argParser.add_argument('-d', '--duration',   type=int, default=4, help='Duration of audio samples in seconds.')

    args = argParser.parse_args()

    tester = AESync(args.ebook_file, args.audio_file, args.output_file, max_l_dist=args.max_l_dist)
    if args.no_generate:
        tester.load()
    else:
        tester.align_book(step_size=args.stepsize, duration=args.duration)
        tester.store()

    tester.validate(count=args.count)
