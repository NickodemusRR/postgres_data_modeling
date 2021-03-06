"""
Udacity Project Modeling Data with Postgres

Date: May 2022
"""

import os
import glob
import psycopg2
import pandas as pd
from sql_queries import song_table_insert, artist_table_insert, time_table_insert, user_table_insert, songplay_table_insert, song_select


def process_song_file(cur, filepath):
    """
    Insert song_data record to database
    """
    # open song file
    songs_df = pd.read_json(filepath, lines=True)

    # insert song record
    song_data = songs_df[['song_id', 'title', 'artist_id',
                          'year', 'duration']].values[0].tolist()
    cur.execute(song_table_insert, song_data)

    # insert artist record
    artist_data = songs_df[['artist_id',
                            'artist_name',
                            'artist_location',
                            'artist_latitude',
                            'artist_longitude']].values[0].tolist()

    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """
    Insert log_data record to database
    """
    # open log file
    log_df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    log_df = log_df[log_df['page'] == 'NextSong']

    # convert timestamp column to datetime
    converted_time = pd.to_datetime(log_df['ts'], unit='ms')

    # insert time data records
    time_data = (
        converted_time,
        converted_time.dt.hour,
        converted_time.dt.day,
        converted_time.dt.weekofyear,
        converted_time.dt.month,
        converted_time.dt.year,
        converted_time.dt.weekday)
    column_labels = (
        'start_time',
        'hour',
        'day',
        'week of year',
        'month',
        'year',
        'weekday')
    time_df = pd.DataFrame(
        {column_labels[i]: time_data[i] for i in range(len(column_labels))})

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = log_df[['userId', 'firstName', 'lastName', 'gender', 'level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for _, row in log_df.iterrows():

        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()

        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (
            pd.to_datetime(row.ts, unit='ms'),
            row.userId,
            row.level,
            songid,
            artistid,
            row.sessionId,
            row.location,
            row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    """
    Processing all data in directory
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root, '*.json'))
        for file in files:
            all_files.append(os.path.abspath(file))

    # get total number of files found
    num_files = len(all_files)
    print(f'{num_files} files found in {filepath}')

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print(f'{i}/{num_files} files processed.')


def main():
    """
    Run etl pipeline
    """
    conn = psycopg2.connect(
        "host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()
