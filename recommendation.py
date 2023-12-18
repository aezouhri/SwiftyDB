import psycopg2

"""Ask @aezouhri for credentials to connect to the database. 
You will need to create a file called `credentials.txt` in the same directory as this file.
DO NOT COMMIT `credentials.txt` TO GITHUB."""


def credentials():
    file1 = open('credentials.txt', 'r')
    lines = file1.readlines()
    username = lines[0].strip()
    password = lines[1].strip()
    file1.close()
    return username, password


# Connect to the database
def create_connection(username, password):
    """ Connect to the PostgreSQL database server """
    conn = None

    try:
        conn = psycopg2.connect(
            host="s-l112.engr.uiowa.edu",
            port="5432",
            database="mdb_student26",
            options="-c search_path=project,public",
            user=username,
            password=password)

        # create a cursor
        cursor = conn.cursor()
        print('Connected to the database.')
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"The error '{e}' occurred")
    return conn


def search_songs(connection, song_name):
    """Search for songs by name."""
    query = "SELECT name, artists, release_date FROM songs WHERE name ILIKE %s LIMIT 3;"
    cursor = connection.cursor()
    cursor.execute(query, ('%' + song_name + '%',))
    return cursor.fetchall()


def recommend_taylor_swift_songs(connection, user_song):
    """Recommend top 3 Taylor Swift songs based on the selected song features."""
    query = """Select acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, tempo, valence
    FROM songs  WHERE name = %s AND artists = %s AND release_date = %s;"""
    cursor = connection.cursor()
    cursor.execute(query, (user_song[0], user_song[1], user_song[2]))
    user_params = cursor.fetchone()  # Fetch the result of the query

    query = """
SELECT 
    grouped.name,
    (
        POW((%s - grouped.avg_acousticness), 2) +
        POW((%s - grouped.avg_danceability), 2) +
        POW((%s - grouped.avg_energy), 2) +
        POW((%s - grouped.avg_instrumentalness), 2) +
        POW((%s - grouped.avg_liveness), 2) +
        POW((%s - grouped.avg_loudness), 2) +
        POW((%s - grouped.avg_speechiness), 2) +
        POW((%s - grouped.avg_tempo), 2) +
        POW((%s - grouped.avg_valence), 2)
    ) AS similarity
FROM 
    (
        SELECT 
            name,
            AVG(acousticness) AS avg_acousticness,
            AVG(danceability) AS avg_danceability,
            AVG(energy) AS avg_energy,
            AVG(instrumentalness) AS avg_instrumentalness,
            AVG(liveness) AS avg_liveness,
            AVG(loudness) AS avg_loudness,
            AVG(speechiness) AS avg_speechiness,
            AVG(tempo) AS avg_tempo,
            AVG(valence) AS avg_valence
        FROM 
            ts_table
        GROUP BY 
            name
    ) AS grouped
ORDER BY 
    similarity ASC
LIMIT 3;
    """
    cursor.execute(query, user_params)
    return cursor.fetchall()


def main():
    username, password = credentials()
    connection = create_connection(username, password)

    song_name = input("Enter a song name to search: ")
    songs = search_songs(connection, song_name)

    print("Select the correct song:")
    for i, song in enumerate(songs, start=1):
        print(f"{i}. {song[0]} by {song[1]}, released on {song[2]}")
    print("4. None of these")

    selection = int(input("Enter the number of your song: "))

    if selection in [1, 2, 3]:
        user_song = songs[selection - 1]  # Retrieve the selected song's details
        # This is where you'd also retrieve the full feature vector for `user_song` from the database
        recommendations = recommend_taylor_swift_songs(connection, user_song)
        print("Top 3 Taylor Swift songs that match your selection:")
        for i, rec in enumerate(recommendations, start=1):
            print(f"{i}. {rec[0]}")
    else:
        print("Feature to import song from Spotify is not yet implemented.")


if __name__ == "__main__":
    main()
