from __future__ import annotations
from typing import List, Dict, Tuple
import mysql.connector, numpy, time

from nltk.corpus import wordnet

from .utils import tag_to_inttag, inttag_to_tag, tokenize_tweet, tag_words, filter_important_words, draw_progress_bar

class BaseModel:
    def __init__(self,
        tweet_count: int,
        hashtags: Dict[str, int],
        hashtag_frequencies: numpy.ndarray,
        words: Dict[str, int],
        word_tags: numpy.ndarray,
        model_id: int):
        self.tweet_count = tweet_count

        self._hashtags = hashtags
        self._hashtags_array = list(hashtags.keys())
        self._words = words
        self._words_array = list(words.keys())

        self.hashtag_frequencies = hashtag_frequencies
        self.word_tags = word_tags

        self.model_id = model_id

    def _get_hashtag_words(self, hashtag: str) -> numpy.ndarray:
        """Returns a list of word counts for a hashtag

        Args:
            hashtag (str): The hashtag string

        Raises:
            NotImplementedError: this function must be overriden

        Returns:
            numpy.ndarray: A numpy array with shape (len(words),)
        """
        raise NotImplementedError

    @property
    def hashtags(self):
        return self._hashtags_array

    @property
    def words(self):
        return self._words_array

    @property
    def word_count(self) -> int:
        """Get the unique word count of the model

        Returns:
            int: The unique word count
        """
        return len(self._words)


    def get_hashtag_string(self, hashtag_id: int) -> str:
        """Get a hashtag's string value from its ID

        Args:
            hashtag_id (int): The hashtag's ID

        Returns:
            str: The string value of the hashtag
        """
        return self.hashtags[int(hashtag_id)]

    def get_word_string(self, word_id: int) -> str:
        """Get a word's string value from its ID

        Args:
            word_id (int): The word's ID

        Returns:
            str: The string value of the word
        """
        return self.words[word_id]

    def text_probability(self, string: str) -> numpy.ndarray:
        """Predict the (relative) probabilities for each hashtag

        Args:
            string (str): The string to predict the probabilities for

        Returns:
            numpy.ndarray: List of relative probabilities with the index of the hashtag ID
        """
        tokenized_tweet = tokenize_tweet(string)
        word_tags = tag_words(tokenized_tweet)
        words_and_tags = zip(*filter_important_words(tokenized_tweet, word_tags))

        hashtag_probabilities = numpy.zeros(len(self.hashtags))
        
        for hashtag in self.hashtags:
            text_hashtag_probability = 1
            for word, inttag in words_and_tags:
                text_hashtag_probability *= self.word_probability(word, inttag, hashtag)
            
            hashtag_probability = self.hashtag_probability(hashtag)
            hashtag_probabilities[self._hashtags[hashtag]] = text_hashtag_probability * hashtag_probability

        return hashtag_probabilities

    def word_probability(self, word: str, inttag: int, hashtag: str) -> int:
        """Predict the (relative) probability for a word given the hashtag

        Args:
            word (str): The word to calculate the probability for
            inttag (int): An integer tag for the word (see .utils.tag_to_inttag)
            hashtag (str): The hashtag to calculate the probability for

        Returns:
            int: An integer of the (relative) probability
        """
        wordcount = 0

        hashtag_words = self._get_hashtag_words(hashtag)
        tag = inttag_to_tag(inttag)

        # Counts up how many of the word appear in the bag of words for the hashtag
        # Includes similar words as partial counts
        if tag != "":
            word_synsets = wordnet.synsets(word, pos=tag)
            if len(word_synsets) != 0:
                for training_word_id in hashtag_words:
                    # NOTE: This could be made more thourough at the cost of some performance in the future
                    training_tag = inttag_to_tag(self.word_tags[training_word_id])
                    training_synsets = wordnet.synsets(self.words[training_word_id], pos=training_tag)
                    if len(training_synsets) != 0:
                        similarity = wordnet.path_similarity(word_synsets[0], training_synsets[0])
                        if similarity != None:
                            wordcount += similarity**2
        
        probability = 1 + wordcount
        probability /= self.hashtag_frequencies[self._hashtags[hashtag]] + len(self.words)

        return probability

    def hashtag_probability(self, hashtag: str) -> int:
        """Predict the (relative) probability for a hashtag in general

        Args:
            hashtag (str): The hashtag to calculate the probability for

        Returns:
            int: The (relative) probability
        """
        probability = self.hashtag_frequencies[self._hashtags[hashtag]]
        probability /= self.tweet_count
        return probability
            

class Model(BaseModel):
    def __init__(self,
        tweet_count: int,
        hashtags: Dict[str, int],
        hashtag_frequencies: numpy.ndarray,
        words: Dict[str, int],
        word_tags: numpy.ndarray,
        relations: numpy.ndarray,
        model_id: int = None):
        if relations.shape != (len(hashtags), len(words)):
            raise TypeError(f"Invalid shape {relations.shape}. Must be (hashtag_count, word_count) : {(len(hashtags), len(words))}")
        if len(hashtags) != len(hashtag_frequencies):
            raise TypeError(f"Hashtag frequencies shape ({len(hashtag_frequencies)}) does not match hashtags shape ({len(hashtags)})")
        if len(words) != len(word_tags):
            raise TypeError(f"Word tags shape ({len(word_tags)}) does not match words shape ({len(hashtags)})")
        super().__init__(
            tweet_count=tweet_count,
            hashtags=hashtags,
            hashtag_frequencies=hashtag_frequencies,
            words=words,
            word_tags=word_tags,
            model_id=model_id
        )
        self.relations = relations

    def _get_hashtag_words(self, hashtag: str) -> numpy.ndarray:
        """Returns a list of word counts for a hashtag

        Args:
            hashtag (str): The hashtag string

        Raises:
            NotImplementedError: this function must be overriden

        Returns:
            numpy.ndarray: A numpy array with shape (len(words),)
        """
        return self.relations[self._hashtags[hashtag]]

    @classmethod
    def build(cls, tweets: List[List[str]], logging: bool = True) -> Model:
        """Build a model from a list of tweets

        Args:
            tweets (List[List[str]]): The list of tweets to use
            logging bool: Whether to log progress in stdout or not

        Returns:
            Model: The model object
        """
        tweet_count = len(tweets)
        hashtags = {}
        hashtag_frequencies = []
        words = {}

        tokenized_tweets = []
        numerized_tweets = [] # hashtag and word strings are converted into int

        # Get all words
        start = time.time()
        if logging: print("Retreiving words")
        for tweet in tweets:
            tweet_words = tokenize_tweet(tweet[0])
            for word in tweet_words:
                try:
                    words[word]
                except KeyError:
                    words[word] = len(words)
            tokenized_tweets.append([tweet_words, tweet[1].split(",")])
        if logging: print(time.time()-start)

        # Tag and filter
        start = time.time()
        if logging: print("Tagging words")
        word_tags = tag_words(words)
        words, word_tags = filter_important_words(words, word_tags) # Here the words list is also converted in a dictionary which is much faster
        word_tags = numpy.array(word_tags, dtype=numpy.int16)
        tokenized_tweets = [
            (filter(lambda word : word in words, tweet_words), tweet[1])
            for tweet in tokenized_tweets
        ]
        if logging: print(time.time()-start)

        # Create hashtag data
        start = time.time()
        if logging: print("Creating hashtag data")
        for index, (_, tweet_hashtags) in enumerate(tokenized_tweets):
            for hashtag in tweet_hashtags:
                try:
                    hashtag_frequencies[hashtags[hashtag]] += 1
                except KeyError:
                    hashtags[hashtag] = len(hashtags)
                    hashtag_frequencies.append(1)
        hashtag_frequencies = numpy.array(hashtag_frequencies, dtype=numpy.int32)
        if logging: print(time.time()-start)

        """
        # Create hashtag data
        start = time.time()
        if logging: print("Creating hashtag data")
        unique_hashtags = {}
        for index, (_, tweet_hashtags) in enumerate(tokenized_tweets):
            for hashtag in tweet_hashtags:
                hashtags.append(hashtag)
                try:
                    unique_hashtags[hashtag]
                except KeyError:
                    unique_hashtags[hashtag] = len(unique_hashtags)
        if logging: print(time.time()-start)

        # Create hashtag frequency data
        start = time.time()
        if logging: print("Creating hashtag frequency data")
        hashtag_frequencies = numpy.zeros(len(unique_hashtags))
        for index, hashtag in enumerate(unique_hashtags):
            hashtag_frequencies[index] = hashtags.count(hashtag)
        hashtags = unique_hashtags
        if logging: print(time.time()-start)
        """

        # Modify tokenized_tweets
        start = time.time()
        if logging: print("Creating numerized tweets")
        numerized_tweets = [
            [[ words[word] for word in tweet[0] ],
            [ hashtags[hashtag] for hashtag in tweet[1] ]]
            for tweet in tokenized_tweets
        ]
        if logging: print(time.time()-start)

        # Create relations data
        start = time.time()
        if logging: print("Creating relations data")
        relations = numpy.zeros((len(hashtags),len(words)), dtype=numpy.int32)
        for index in range(len(numerized_tweets)):
            for word_index in range(len(numerized_tweets[index][0])):
                for hashtag_index in range(len(numerized_tweets[index][1])):
                    relations[
                        numerized_tweets[index][1][hashtag_index]
                    ][
                        numerized_tweets[index][0][word_index]
                    ] += 1
        if logging: print(time.time()-start)

        if logging: print("Model built!")
        return Model(
            tweet_count=tweet_count,
            hashtags=hashtags,
            hashtag_frequencies=hashtag_frequencies,
            words=words,
            word_tags=word_tags,
            relations=relations
        )

    @classmethod
    def load(cls, database: mysql.connector.MySQLConnection, model_id: int) -> Model:
        """Load a model from a MySQL database

        Args:
            database (mysql.connector.MySQLConnection): The MySQL database connection to use
            model_id (int): ID of the model to load

        Returns:
            Model: The loaded model object
        """
        cursor = database.cursor()

        # Fetch model tweet count
        cursor.execute(
            "SELECT tweet_count FROM models WHERE id=%s",
            (model_id,)
        )
        tweet_count = cursor.fetchall()[0][0]

        # Fetch hashtags and hashtag frequencies
        cursor.execute(
            f"SELECT * FROM hashtags_{model_id} ORDER BY id ASC"
        )
        hashtags_data = cursor.fetchall()

        # Fetch words and word tags
        cursor.execute(
            f"SELECT * FROM words_{model_id} ORDER BY id ASC"
        )
        words_data = cursor.fetchall()

        # Fetch relations
        cursor.execute(
            f"SELECT * FROM relations_{model_id} ORDER BY hashtag_id ASC, word_id ASC"
        )
        relations_data = cursor.fetchall()

        # Convert data into correct types
        hashtags = {}
        for hashtag in hashtags_data:
            hashtags[hashtag[1]] = len(hashtags)
        hashtag_frequencies = numpy.array([ hashtag[2] for hashtag in hashtags_data ])
        
        words = {}
        for word in words_data:
            words[word[1]] = len(words)
        word_tags = numpy.array([ word[2] for word in words_data ], dtype=numpy.int16)

        relations = numpy.zeros((len(hashtags),len(words)), dtype=numpy.int32)
        for hashtag_id, word_id, frequency in relations_data:
            relations[hashtag_id][word_id] = frequency

        cursor.close()
        
        return Model(
            tweet_count=tweet_count,
            hashtags=hashtags,
            hashtag_frequencies=hashtag_frequencies,
            words=words,
            word_tags=word_tags,
            relations=relations,
            model_id=model_id
        )

    def save(self, database: mysql.connector.MySQLConnection, model_id: int = None) -> int:
        """Save the model to a MySQL databse

        Args:
            database (mysql.connector.MySQLConnection): The MySQL database connection to use
            model_id (int, optional): The model ID to use (overwrites if the model ID already exists). If None then AUTO_INCREMENT is used. Defaults to None.

        Returns:
            int: The model ID of the saved model
        """
        cursor = database.cursor()
        if model_id == None: # Can be 0 so has to use an operator
            cursor.execute(
                "INSERT INTO models (tweet_count) VALUES (%s)",
                (self.tweet_count,)
            )
        else:
            cursor.execute(
                """
                INSERT INTO models (id, tweet_count) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                tweet_count=%s
                """,
                (model_id, self.tweet_count, self.tweet_count)
            ) 
        database.commit()
        if model_id == None:
            model_id = cursor.lastrowid
        
        # Create tables
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS hashtags_{model_id} (
            id MEDIUMINT UNSIGNED NOT NULL UNIQUE AUTO_INCREMENT PRIMARY KEY,
            hashtag VARCHAR(1120) NOT NULL UNIQUE,
            frequency MEDIUMINT UNSIGNED NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
        """)
        cursor.execute(f"TRUNCATE TABLE hashtags_{model_id}")
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS words_{model_id} (
            id MEDIUMINT UNSIGNED NOT NULL UNIQUE AUTO_INCREMENT PRIMARY KEY,
            word VARCHAR(1120) NOT NULL UNIQUE,
            tag TINYINT UNSIGNED NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
        """)
        cursor.execute(f"TRUNCATE TABLE words_{model_id}")
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS relations_{model_id} (
            hashtag_id MEDIUMINT UNSIGNED NOT NULL,
            word_id MEDIUMINT UNSIGNED NOT NULL,
            frequency MEDIUMINT UNSIGNED NOT NULL,
            PRIMARY KEY (hashtag_id, word_id)
        );
        """)
        cursor.execute(f"TRUNCATE TABLE relations_{model_id}")
        database.commit()

        # Save hashtags and hashtag frequencies
        for index, hashtag in enumerate(self.hashtags):
            cursor.execute(
                f"""
                INSERT INTO hashtags_{model_id} (hashtag, frequency) VALUES (%s, %s)
                """,
                (hashtag, self.hashtag_frequencies[index])
            )
        database.commit()

        # Save words and word tags
        for index, word in enumerate(self._words):
            cursor.execute(
                f"""
                INSERT INTO words_{model_id} (word, tag) VALUES (%s, %s)
                """,
                (word, int(self.word_tags[index]))
            )
        database.commit()

        # Save relations
        for (hashtag_id, word_id), frequency in numpy.ndenumerate(self.relations):
            if frequency: # Don't save values of 0 frequency
                cursor.execute(
                    f"""
                    INSERT INTO relations_{model_id} (hashtag_id, word_id, frequency) VALUES (%s, %s, %s)
                    """,
                    (hashtag_id, word_id, frequency)
                )
        database.commit()

        cursor.close()
        return model_id


