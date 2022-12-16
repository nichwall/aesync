#pragma once

#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <dirent.h>
#include <utility>
#include <vector>
#include "util.h"

using namespace std;

pair<string, string> wordSearch(DIR *dp, string query);
pair<string, string> phraseSearch(DIR *dp, string query, int numWords);
int levenshteinDistance(string query, string current);

//compares every word in each file to the query and returns the file and
//sentence that contains the "closest" word to the query
pair<string, string> wordSearch(DIR *dp, string query) {
  pair<string, string> location;
  struct dirent *ent;
  string word;
  string current;
  string fileName;
  string newFileName;
  int bestDistance = 9999;
  int currDistance;

  //continue until no files remain to be read
  while((ent = readdir (dp)) != NULL) {
    fileName = ent->d_name;

    //ignore the home and last directory in "/content"
    if (fileName != "." && fileName != "..") {

      //find where the file extension starts and remove from fileName
      size_t lastIndex = fileName.find_last_of(".");
      newFileName = fileName.substr(0, lastIndex);

      //calculate Levenshtein Distance between query and file name
      currDistance = levenshteinDistance(query, newFileName);

      //if an exact match, update and return location
      if (currDistance == 0 ) {
        location = setLocation(fileName);
        return location;
      }

      //if the "distance" between query and the file name is the smallest
      //distance so far, update location and bestDistance
      if (currDistance <= bestDistance) {
        bestDistance = currDistance;
        location = setLocation(fileName);
      }

      string directory = "./content/";
      newFileName = directory + fileName;
      ifstream file;
      file.open(newFileName);

      //use getline to retrieve sentences from current file until no sentences
      //remain
      while (getline(file, current, '.')) {
        current = trim_string(current);

        //error checking/fixing
        if (current[0] == '\"') {
          if (current[1] == '\n') {
            if (current[2] == '\n')
              current.erase(0,3);
          }
        }

        //add a period if there is no period in current sentence
        if (current.back() != '.')
          current.push_back('.');
        istringstream iss(current);

        //use getline to retrieve every word from the current sentence
        while (getline(iss, word, ' ')) {
          word = trim_string(word);

          //calculate Levenshtein Distance between query and the current word
          currDistance = levenshteinDistance(query, word);

          //if an exact match, update and return location
          if (currDistance == 0 ) {
            location = setLocation(fileName, current);
            return location;
          }

          //if the "distance" between query and the file name is the smallest
          //distance so far, update
          if (currDistance < bestDistance) {
            bestDistance = currDistance;
            location = setLocation(fileName, current);
          }
        }

        //clear the current sentence before moving on in case it is not empty
        current.clear();
      }

      //if at end of file and last sentence does not end with a period,
      //check Levenshtein Distance and update location and bestDistance if
      //necessary
      if (!current.empty()) {
        istringstream iss(current);
        while (getline(iss, word, ' ')) {
          currDistance = levenshteinDistance(query, word);
          if (currDistance < bestDistance) {
            bestDistance = currDistance;
            location = setLocation(fileName, current);
          }
          current.clear();
        }
      }
    }
  }
  return location;
}

//moves through every sentence in every file, breaking up the sentences
//into chunks the size of the query and calculating the distance between
//those chunks and the query
pair<string, string> phraseSearch(DIR *dp, string query, int numWords) {
  pair<string, string> location;
  struct dirent *ent;
  string current;
  string tempCurrent;
  string fileName;
  string newFileName;
  string chunk;
  string word;
  int bestDistance = 9999;
  int currDistance;

  //continue until no files remain to be read
  while((ent = readdir (dp)) != NULL) {
    fileName = ent->d_name;

    //ignore the home and last directory in "/content"
    if (fileName != "." && fileName != "..") {

      //find where the file extension starts and remove from fileName
      size_t lastIndex = fileName.find_last_of(".");
      newFileName = fileName.substr(0, lastIndex);

      //calculate Levenshtein Distance between query and file name
      currDistance = levenshteinDistance(query, newFileName);

      //if an exact match, update and return location
      if (currDistance == 0 ) {
        location = setLocation(fileName);
        return location;
      }

      //if the "distance" between query and the file name is the smallest
      //distance so far, update location and bestDistance
      if (currDistance <= bestDistance) {
        bestDistance = currDistance;
        location = setLocation(fileName);
      }

      string directory = "./content/";
      newFileName = directory + fileName;
      ifstream file;
      file.open(newFileName);

      //use getline to retrieve sentences from current file until no sentences
      //remain
      while (getline(file, current, '.')) {
        current = trim_string(current);

        //error checking/fixing
        if (current[0] == '\"') {
          if (current[1] == '\n') {
            if (current[2] == '\n')
              current.erase(0,3);
            else
              current.erase(0,2);
          }
        }

        //if sentence does not have a period at then end, add one
        if (current.back() != '.')
          current.push_back('.');
        tempCurrent = current;
        stringstream iss(tempCurrent);

        //while the current sentence chunk has not reached the end of the
        //sentence
        while (chunk.back() != '.') {
          chunk.clear();
          int i = 0;

          //add words from the current sentence to chunk until the number
          //of words in query and chunk are equal
          while (i < numWords) {
            iss >> word;
            if (!chunk.empty())
              chunk = chunk + ' ' + word;
            else
              chunk = word;
            i++;
          }

          chunk = trim_string(chunk);

          //calculate Levenshtein Distance between query and the current word
          currDistance = levenshteinDistance(query, chunk);

          //if an exact match, update and return location
          if (currDistance == 0 ) {
            location = setLocation(fileName, current);
            return location;
          }

          //if the "distance" between query and the file name is the smallest
          //distance so far, update
          if (currDistance < bestDistance) {
            bestDistance = currDistance;
            location = setLocation(fileName, current);
          }

          //cut out our 1/4 of the number of words in the query from the
          //beginning of the current string
          for (int j = 0; j <= (numWords / 4); j++)
            tempCurrent = tempCurrent.substr(tempCurrent.find_first_of(" \t\n") + 1);
          iss.str("");
          iss.clear();
          iss << tempCurrent;
        }
        chunk.clear();
      }
    }
  }
  return location;
}

//calculate the Levenshtein Distance between two strings
//return result as an int
int levenshteinDistance(string query, string current) {
  unsigned int deletionCost;
  unsigned int insertionCost;
  unsigned int substitutionCost;
  const size_t len1 = query.length();
  const size_t len2 = current.length();

  //create two work vectors with the distance of the string we are comparing
  //query to
  vector<unsigned int> prevRow(len2 + 1);
  vector<unsigned int> row(len2 + 1);

  //initialize prevRow (previous row of distances)
  for (unsigned int i = 0; i <= len2; i++)
    prevRow[i] = i;

  for (unsigned int i = 0; i < len1; i++) {

    //calculate row (current row distances) from prevRow
    row[0] = i + 1;

    //fill in row
    for (unsigned int j = 0; j < len2; j++) {

      //calculate costs
      deletionCost = prevRow[j + 1] + 1;
      insertionCost = row[j] + 1;
      if (query[i] == current[j])
        substitutionCost = prevRow[j];
      else
        substitutionCost = prevRow[j] + 1;

      row[j + 1] = min(min(deletionCost, insertionCost), substitutionCost);
    }

    //copy row to prevRow for next iteration
    swap(row, prevRow);
  }

  //after last swap, results of row are in prevRow
  return prevRow[len2];
}