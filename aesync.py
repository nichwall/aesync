from fuzzysearch import find_near_matches_in_file, find_near_matches
import subprocess
import time
import csv
from random import randint

import whisper

class AESync:
    def __init__(self, fname_ebook, fname_audio):
        self.fname_ebook = fname_ebook
        self.fname_audio = fname_audio
        
        self.mapping = []

        self.model = whisper.load_model("base")

        self.ebook_size   = 0
        self.audio_length = 0

        self.temp_dir = "work"

    def convert_ebook(self):
        # Get file format of ebook
        ebook_format = self.fname_ebook.split(".")[-1]

        if ebook_format == "epub":
            # Convert epub to txt using epub2txt2
            cmd = f"""./epub2txt2/epub2txt "{self.fname_ebook}" > {self.temp_dir}/input.txt"""
        elif ebook_format == "txt":
            # Just copy the book if text file
            cmd = f"""cp "{self.fname_ebook}" {self.temp_dir}/input.txt"""

        subprocess.run(cmd, shell=True)

        with open(f"{self.temp_dir}/input.txt",'r') as f:
            self.ebook_size = len(f.read())

    def get_audio_length(self):
        # Get length of audio file in seconds
        cmd = f"""ffprobe -i "{self.fname_audio}" -show_format -v quiet | sed -n 's/duration=//p'"""
        ret_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.split()[-1]

        self.audio_length = float(ret_output)

    def extract_snippet(self, start, duration=10):
        # Extract to a temp file
        temp_filename = f"{self.temp_dir}/seg_{start}.wav"
        cmd = f"""ffmpeg -y -loglevel panic -ss {start} -to {start+duration} -i "{self.fname_audio}" "{temp_filename}" """

        # Run command
        subprocess.run(cmd, shell=True)

        # Transcribe audio
        #cmd = f"spchcat {temp_filename}"
        #ret_output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        result = self.model.transcribe(temp_filename)
        print(f" Result: {result['text']}")

        return result["text"]

    def align_book(self, step_size=1000, duration=10):
        # Ensure ebook is converted
        if self.ebook_size == 0:
            self.convert_ebook()

        # Ensure we have the audio length
        if self.audio_length == 0:
            self.get_audio_length()

        # Iterate over the book and get snippets
        for start in range(100, int(self.audio_length)-duration, step_size):
            position = self.get_position(start, duration)
            print(f"Position: {position}")

    def get_position(self, start, duration):
        # Extract the snippet
        search_str = self.extract_snippet(start, duration=duration)

        # Figure out percentage of audiobook position
        audiobook_percentage = start / self.audio_length
        # Once we have this percentage, subtract 3% for searching in text
        audiobook_percentage -= 0.05
        if audiobook_percentage < 0:
            audiobook_percentage = 0

        # Use percentage to get starting point of where to look
        text_start_loc = int( audiobook_percentage      * self.ebook_size)
        text_end_loc   = int((audiobook_percentage+0.1) * self.ebook_size)
        if text_end_loc > self.ebook_size:
            text_end_loc = self.ebook_size

        with open(f"{self.temp_dir}/input.txt", 'r') as f:
            text_search = f.read()[text_start_loc:text_end_loc]

        # Look for search string in subsection
        try:
            nearest = find_near_matches(search_str, text_search, max_l_dist=7)
            # Adjust start position by actual start position
            return nearest[0].start + text_start_loc
        except:
            return -1

if __name__ == "__main__":
    BOOKNAME = "Sufficiently Advanced Magic"
    tester = AESync(f"{BOOKNAME}.epub", f"{BOOKNAME}.m4a")
    tester.align_book(step_size=10000, duration=4)
