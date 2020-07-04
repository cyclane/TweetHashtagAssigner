from typing import List, Dict
from __future__ import annotations
import mysql.connector
import numpy

from .utils import tag_to_inttag, tokenize_tweet, tag_words, filter_important_words

class Model:
    def __init__(self,
        tweet_count: int,
        hashtags: List[str],
        hashtag_frequencies: numpy.ndarray,
        words: List[str],
        word_tags: numpy.ndarray,
        relations: numpy.ndarray,
        model_id: int = None):
        if relations.shape != (len(hashtags), len(words)):
            raise TypeError(f"Invalid shape {relations.shape}. Must be (hashtag_count, word_count) : {(len(hashtags), len(words))}")
        if len(hashtags) != len(hashtag_frequencies):
            raise TypeError(f"Hashtag frequencies shape ({len(hashtag_frequencies)}) does not match hashtags shape ({len(hashtags)})")
        if len(words) != len(word_tags):
            raise TypeError(f"Word tags shape ({len(word_tags)}) does not match words shape ({len(hashtags)})")

        self.tweet_count = tweet_count
        self.hashtags = hashtags
        self.words = words

        self.hashtag_frequencies = hashtag_frequencies
        self.word_tags = word_tags

        self.relations = relations

        self.model_id = model_id

    @classmethod
    def build(cls, tweets: List[List[str]]) -> Model:
        """Build a model from a list of tweets

        Args:
            tweets (List[List[str]]): The list of tweets to use

        Returns:
            Model: The model object
        """
        tweet_count = len(tweets)
        hashtags = []
        hashtag_frequencies = numpy.array([]) 
        words = []

        # Get all words
        tokenized_tweets = []
        for tweet in tweets:
            tweet_words = tokenize_tweet(tweet[0])
            for word in tweet_words:
                if word not in words:
                    words.append(word)
            tokenized_tweets.append((tweet_words, tweet[1]))

        # Tag and filter
        word_tags = tag_words(*words)
        words, word_tags = filter_important_words(words, word_tags)

        word_tags = numpy.array(word_tags)

        tokenized_tweets = [
            (filter(lambda word : word in words, tweet_words), tweet[1])
            for tweet in tokenized_tweets
        ]

        # Create relations with a dummy row (for concatenate to work)
        relations = numpy.zeros((1,len(words)))

        # createe hashtag, hashtag requency and relations data
        for tweet in tokenized_tweets:
            tweet_words = tweet[0]
            tweet_hashtags = tweet[1].split(",")
            for hashtag in tweet_hashtags:
                if hashtag not in hashtags:
                    # Add hashtag to list and change shapes of affected numpy arrays
                    hashtags.append(hashtag)
                    hashtag_frequencies = numpy.concatenate((
                        hashtag_frequencies,
                        (1,)
                    ))
                    relations = numpy.concatenate((
                        relations,
                        numpy.zeros((1,len(words)))
                    ))
                else:
                    hashtag_frequencies[hashtags.index(hashtag)] += 1

                for word in tweet_words:
                    relations[hashtags.index(hashtag)+1][words.index(word)] += 1

        relations = numpy.delete(relations, 0, axis=0)

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
        cursor.exectue(
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
        hashtags = [ hashtag[1] for hashtag in hashtags_data ]
        hashtag_frequencies = numpy.array([ hashtag[2] for hashtag in hashtags_data ])
        
        words = [ word[1] for word in words_data ]
        word_tags = numpy.array([ word[2] for word in words ])

        # This will work because data is already in the correct order because of the ORDER BY keyword in the SQL query
        relations = numpy.reshape(
            [ relation[2] for relation in relations_data ],
            (len(hashtags), len(words))
        )

        return Model(
            tweet_count=tweet_count,
            hashtags=hashtags,
            hashtag_frequencies=hashtag_frequencies,
            words=words,
            word_tags=word_tags,
            relations=relations,
            model_id=model_id
        )

    @property
    def word_count(self) -> int:
        """Get the unique word count of the model

        Returns:
            int: The unique word count
        """
        return len(self.words)

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
        
        TRUNCATE TABLE hashtags_{model_id};
        """)
        cursor.execute(f"""
        CREATE TABLE words_{model_id} (
            id MEDIUMINT UNSIGNED NOT NULL UNIQUE AUTO_INCREMENT PRIMARY KEY,
            word VARCHAR(1120) NOT NULL UNIQUE,
            tag TINYINT UNSIGNED NOT NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

        TRUNCATE TABLE words_{model_id};
        """)
        cursor.execute(f"""
        CREATE TABLE relations_{model_id} (
            hashtag_id MEDIUMINT UNSIGNED NOT NULL,
            word_id MEDIUMINT UNSIGNED NOT NULL,
            frequency MEDIUMINT UNSIGNED NOT NULL,
            PRIMARY KEY (hashtag_id, word_id)
        );

        TRUNCATE TABLE relations_{model_id};
        """)
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
        for index, word in enumerate(self.words):
            cursor.execute(
                f"""
                INSERT INTO words_{model_id} (word, tag) VALUES (%s, %s)
                """,
                (word, self.word_tags[index])
            )
        database.commit()

        # Save relations
        for (hashtag_id, word_id), frequency in numpy.ndenumerate(self.relations):
            cursor.execute(
                f"""
                INSERT INTO relations_{model_id} (hashtag_id, word_id, frequency) VALUES (%s, %s, %s)
                """,
                (hashtag_id, word_id, frequency)
            )
        database.commit()

        return model_id


