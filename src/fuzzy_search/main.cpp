#include "search.h"
#include "util.h"

using namespace std;

int main() {
	DIR *dp;
	string query;
	pair<string, string> location;
	int numWords;

	query = getQuery();
	query = trim_string(query);

	
	numWords = countWords(query);
	if((dp = opendir("./content")) != NULL) {
		if (numWords == 1)
			location = wordSearch(dp, query);
		else
			location = phraseSearch(dp, query, numWords);
		printOutput(location);
	}
	else if(dp == NULL) {
		closedir(dp);
		perror("Couldn't open the directory!");
	}
	
	closedir(dp);
	return 0;
}