# aesync

This utility was designed to accept an e-book file and an audiobook file and generate sync points every few minutes. The main reason for this is transcribing a full length audio book takes quite a while, and most narrators read at a relatively constant speed. A simple percentage of the book is difficult, due to differences in format (pictures, chapter breaks, extra preface or postface material).

This utility requires ffmpeg, unzip, [epub2txt2][https://github.com/kevinboone/epub2txt2], and [spchcat][https://github.com/petewarden/spchcat] to function.
The fuzzy search uses Levenshtein Distance and is adapted from [Fuzzy-Search][https://github.com/andrewpadg/Fuzzy-Search].

# Program flow
1. Convert epub to txt
2. Extract 10 second chunks from the input audio
3. Convert audio chunks into text
4. Fuzzy search of transcribed text in book text file
5. Map time stamps to percentage of e-book (based on character count)
6. Write to file

# Future Work
[ ] Support more ebook formats
[ ] Make audio chunks configurable
[ ] Add more output formats
[ ] Add more language support
