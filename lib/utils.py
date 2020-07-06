from typing import Any, List, Dict, Tuple
from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.tokenize import TweetTokenizer
from nltk.stem.wordnet import WordNetLemmatizer
import mysql.connector, sys, numpy


def tag_to_inttag(tag: Any) -> int:
    """Convert WordNet tag to a tag integer

    Args:
        tag (Any): The WordNet tag to convert

    Returns:
        int: The integer 
    """
    tags = [
        wn.NOUN,
        wn.VERB,
        wn.ADJ,
        wn.ADV,
        ""
    ]
    try:
        return tags.index(tag)
    except:
        return tags.index("")


def inttag_to_tag(integer: int) -> Any:
    """Convert tag integer to a WordNet tag

    Args:
        integer (int): The tag integer to convert

    Returns:
        Any: The WordNet tag
    """
    tags = [
        wn.NOUN,
        wn.VERB,
        wn.ADJ,
        wn.ADV,
        ""
    ]
    try:
        return tags[integer]
    except:
        return ""

def str_to_inttag(string: str) -> int:
    """Convert string to a tag integer

    Args:
        string (str): The string to convert

    Returns:
        int: [description]
    """
    tags = [
        "N",
        "V",
        "J",
        "R",
        ""
    ]
    try:
        return tags.index(string)
    except:
        return tags.index("")

def tokenize_tweet(tweet: str) -> List[str]:
    """Tokenize a tweet into words

    Args:
        tweet (str): The string of the tweet

    Returns:
        List[str]: The list of words
    """
    # NOTE: I'm not sure TweetTokenizer is actually useful here, might just change it to word tokenizer later
    tokenizer = TweetTokenizer(preserve_case=False)
    tokens = tokenizer.tokenize(tweet)

    # Lemmatize the words
    #lemmatizer = WordNetLemmatizer()
    #simple_words = [lemmatizer.lemmatize(token) for token in tokens]

    return tokens

def tag_words(words: List[str]) -> List[int]:
    """Tag words by part of speech

    Args:
        words (List[str]): A list of words to tag

    Returns:
        List[int]: A list of integer tags (or None if not tag was assigned)
    """
    word_tags = pos_tag(words)

    # Remove conjunctions, determiners, etc.
    # Full list of what the tags mean at https://medium.com/@muddaprince456/categorizing-and-pos-tagging-with-nltk-python-28f2bc9312c3
    # Also then change the pos tags to be compatible with wordnet
    tags = []
    for _, tag in word_tags:
        if tag not in {'CC', 'DT', 'EX', 'IN', 'LS', 'MD', 'PDT', 'POS', 'PRP', 'PRP$', 'RP', 'TO', 'UH', 'WDT', 'WP', 'WP$', 'WRB'}:
            tags.append(str_to_inttag(tag[0]))
        else:
            tags.append(None)

    return tags

def filter_important_words(words: List[str], tags: List[int]) -> Tuple[Dict[str, int], List[int]]:
    """Filter out unimportant words
    Unimportant words are ones with a tag of None

    Args:
        words (List[str]): The list of words
        tags (List[int]): The list of tags of the words

    Returns:
        Tuple[Dict[str, int], List[int]]: A tuple of the filtered list of (words, tags)
    """
    filtered_words = {}
    filtered_tags = []
    
    for word, tag in zip(words, tags):
        if tag != None:
            filtered_words[word] = len(filtered_words)
            filtered_tags.append(tag)
    
    return (filtered_words, filtered_tags)

def load_tweets(database: mysql.connector.MySQLConnection) -> List[Tuple[str,str]]:
    """Download tweets from a MySQL database

    Args:
        database (mysql.connector.MySQLConnection): The MySQL database connection to use

    Returns:
        List[Tuple[str,str]]: A list of tweets (content, hashtags)
    """
    cursor = database.cursor()
    cursor.execute("SELECT content, hashtags FROM tweets")
    tweets = cursor.fetchall()
    cursor.close()
    return tweets

def draw_progress_bar(percentage, width=20):
    sys.stdout.write("\r")
    sys.stdout.write("[{:<{}}] {:.0f}%".format("=" * int(width * percentage), width, percentage * 100))
    sys.stdout.flush()

def sort_probabilities(probabilities: numpy.ndarray) -> numpy.ndarray:
    """Sort a list of probabilities

    Args:
        probabilities (numpy.ndarray): List of probabilities (shape is (n,))

    Returns:
        numpy.ndarray: The list of probabilities sorted by highest probability (shape is (n,2))
    """
    sorted_probabilities = numpy.vstack((
        numpy.arange(len(probabilities)),
        probabilities
    )).T # Transpose is required to make it a horizontal stack instead of vertical stack
    sorted_probabilities = sorted_probabilities[sorted_probabilities[:,1].argsort()] # Sorts the new array by the second column (which contains the probability)
    return sorted_probabilities