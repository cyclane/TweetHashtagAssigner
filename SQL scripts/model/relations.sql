CREATE TABLE relations (
    hashtag_id MEDIUMINT UNSIGNED NOT NULL,
    word_id MEDIUMINT UNSIGNED NOT NULL,
    frequency MEDIUMINT UNSIGNED NOT NULL,
    PRIMARY KEY (hashtag_id, word_id)
);