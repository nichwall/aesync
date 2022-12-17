# AESync

This utility was designed to accept an e-book file and an audiobook file and generate sync points every few minutes. The main reason for this is transcribing a full length audio book takes quite a while, and this should account for inconsistencies in reading speed or content differents (an image in the ebook is read by the narrator, table of contents, mismatched content).

This utility requires ffmpeg, unzip, [fuzzysearch](https://pypi.org/project/fuzzysearch/), [epub2txt2](https://github.com/kevinboone/epub2txt2), and [OpenAI Whisper](https://github.com/openai/whisper).

## File limitations
Input files:
- Only EPUB files are supported
- Any single track audio file supported by ffmpeg

Output files:
- Only CSVs are currently generated

# Setup instructions
Clone this repository and run the `setup.sh` script to configure epub2txt2 and put the compiled binary where AESync expects it to be. Then depending on whether using pip or pip3, install the Python dependencies using `pip install -r requirements.txt`.

# Usage
Run `aesync.py -h` using your favorite terminal and Python 3 to see the command line arguments.

# Program flow
1. Convert epub to txt
2. Extract small chunks from the input audio
3. Convert audio chunks into text
4. Fuzzy search of transcribed text in book text file
5. Map time stamps to percentage of e-book (based on character count)
6. Write mapping to file

# Future Work
[ ] Support more ebook formats

[x] Make audio chunks configurable

[ ] Add more output formats

[ ] Add more language support
