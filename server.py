import json
import os
from datetime import datetime

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS  # Import CORS
import psycopg2
import requests
import base64
import config as cfg
from pymongo import MongoClient
from neo4j import GraphDatabase
from neo4j_playlist_similarity import find_songs_for_playlist

# Spotify API credentials
CLIENT_ID = cfg.client_id
CLIENT_SECRET = cfg.client_secret

app = Flask(__name__)
CORS(app)  # Enable CORS for the Flask app
app.secret_key = os.urandom(24)  # Or set a static secret key

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["MDB_Project"]
playlist_collection = db["playlists"]

# neo4j connection
newo4j_uri = "neo4j://localhost:7687"
newo4j_user = "neo4j"
newo4j_password = "swiftydb"


def credentials():
    """
    This function reads the database credentials from a file named 'credentials.txt'.
    The first line of the file should contain the username and the second line should contain the password.
    It returns a tuple containing the username and password.
    """
    with open("credentials.txt", "r") as file1:
        lines = file1.readlines()
        username = lines[0].strip()
        password = lines[1].strip()
    return username, password


def create_connection():
    """
    This function creates a connection to the PostgreSQL database.
    It first retrieves the username and password from the credentials function.
    Then, it tries to establish a connection to the database using these credentials.
    If the connection is successful, it returns the connection object.
    If there is an error during the connection, it prints the error and returns None.
    """
    username, password = credentials()
    try:
        conn = psycopg2.connect(
            host="s-l112.engr.uiowa.edu",
            port="5432",
            database="mdb_student26",
            options="-c search_path=project,public",
            user=username,
            password=password,
        )
        return conn
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"The error '{e}' occurred")
        return None


@app.route("/")
def index():
    if session.get("user_id") is None:
        session["user_id"] = os.urandom(
            16
        ).hex()  # Generate a new user ID for the session
    return render_template("index.html")


@app.route("/search-songs")
def search_songs_page():
    return render_template("search_songs.html")


@app.route("/api/search-songs", methods=["GET"])
def search_songs():
    """
    This function handles the GET request to the "/api/search-songs" endpoint.
    It takes two query parameters: "song" and "artist".
    It connects to the PostgreSQL database and searches for songs that match the provided song name and artist name.
    It returns a JSON list of songs that match the search criteria.
    """
    connection = create_connection()
    if connection:
        song_name = request.args.get("song")
        artist_name = request.args.get("artist")
        cursor = connection.cursor()
        query = "SELECT name, artists, release_date FROM songs WHERE name ILIKE %s and artists ILIKE %s LIMIT 5;"
        cursor.execute(
            query,
            (
                "%" + song_name + "%",
                "%" + artist_name + "%",
            ),
        )
        songs = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(songs)
    else:
        print("Error in the connection")
        return jsonify([])


@app.route("/api/taylor-swift-recommendations", methods=["POST"])
def recommend_taylor_swift_songs():
    """
    This function recommends Taylor Swift songs based on the user's song preference.
    It receives a POST request with the user's song as JSON.
    It connects to the database, fetches the song parameters, and calculates the similarity with Taylor Swift's songs.
    It then returns the top 3 most similar Taylor Swift songs.
    """
    user_song = request.json
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = """Select acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, tempo, valence
    FROM songs  WHERE name = %s AND artists = %s AND release_date = %s;"""
        cursor.execute(query, (user_song[0], user_song[1], user_song[2]))
        user_params = cursor.fetchone()

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
        recommendations = cursor.fetchall()
        print(recommendations, "recommendations")
        cursor.close()
        connection.close()
        return jsonify(recommendations)
    else:
        return jsonify([])


# Get Spotify access token
def get_spotify_token():
    #

    """
    This function is used to get the Spotify access token. It first encodes the client ID and secret into base64 format.
    Then, it sends a POST request to the Spotify API with the encoded credentials to get the access token.
    The function returns the access token received from the Spotify API.
    """

    message = f"{CLIENT_ID}:{CLIENT_SECRET}"
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")

    headers = {
        "Authorization": f"Basic {base64_message}",
    }

    data = {"grant_type": "client_credentials"}

    response = requests.post(
        "https://accounts.spotify.com/api/token", headers=headers, data=data
    )
    # print(response.json(), "response")
    return response.json().get("access_token")


# Search for songs on Spotify
@app.route("/api/search-spotify", methods=["GET"])
def search_spotify():
    """
    This function is used to search for songs on Spotify. It takes the song name and artist name as parameters from the request.
    It then makes a request to the Spotify API to search for the song. The function returns a JSON response containing the top 5 results.
    """
    song_name = request.args.get("song")
    artist_name = request.args.get("artist")
    headers = {
        "Authorization": f"Bearer {get_spotify_token()}",
    }
    spotify_query = ""
    if artist_name:
        spotify_query += f" artist:{artist_name}"
    if song_name:
        spotify_query += f" track:{song_name}"
    params = (
        ("q", spotify_query),
        ("type", "track"),
        ("limit", "5"),
    )

    response = requests.get(
        "https://api.spotify.com/v1/search", headers=headers, params=params
    )
    # print(response.json(), " :response from spotify")
    tracks = response.json().get("tracks", {}).get("items", [])
    songs = []
    for track in tracks:
        song = {
            "id": track["id"],
            "name": track["name"],
            "release_date": track["album"]["release_date"],
            "artists": [artist["name"] for artist in track["artists"]],
        }
        songs.append(song)
    return jsonify(songs)


# Add song from Spotify to database
@app.route("/api/add-spotify-song", methods=["POST"])
def add_spotify_song():
    """
    This function handles the POST request at the /api/add-spotify-song endpoint.
    It takes a song JSON object from the request, retrieves the song ID, and makes a request to the Spotify API to get the audio features of the song.
    The function then adds these audio features to the song data and inserts the song into the PostgreSQL database.
    """
    song = request.json
    print(song, "song")
    song_id = song.get("id")  # Assuming the song ID is included in the JSON
    headers = {
        "Authorization": f"Bearer {get_spotify_token()}",
    }

    # Get audio features for the song
    audio_features_response = requests.get(
        f"https://api.spotify.com/v1/audio-features/{song_id}", headers=headers
    )
    audio_features = audio_features_response.json()

    # Add audio features to the song data
    song.update(
        {
            "acousticness": audio_features["acousticness"],
            "danceability": audio_features["danceability"],
            "energy": audio_features["energy"],
            "instrumentalness": audio_features["instrumentalness"],
            "liveness": audio_features["liveness"],
            "loudness": audio_features["loudness"],
            "speechiness": audio_features["speechiness"],
            "tempo": audio_features["tempo"],
            "valence": audio_features["valence"],
            "duration_ms": audio_features["duration_ms"],
        }
    )
    song_good = {
        "name": song["name"],
        "release_date": song["release_date"],
        "artists": song["artists"],
        "acousticness": song["acousticness"],
        "danceability": song["danceability"],
        "energy": song["energy"],
        "instrumentalness": song["instrumentalness"],
        "liveness": song["liveness"],
        "loudness": song["loudness"],
        "speechiness": song["speechiness"],
        "tempo": song["tempo"],
        "valence": song["valence"],
        "duration_ms": song["duration_ms"],
    }
    # Add song to database
    # You'll need to implement this
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = """INSERT INTO songs (name, artists, release_date, acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, tempo, valence, duration_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        cursor.execute(
            query,
            (
                song_good["name"],
                str(song_good["artists"]).strip("['']"),
                song_good["release_date"],
                song_good["acousticness"],
                song_good["danceability"],
                song_good["energy"],
                song_good["instrumentalness"],
                song_good["liveness"],
                song_good["loudness"],
                song_good["speechiness"],
                song_good["tempo"],
                song_good["valence"],
                song_good["duration_ms"],
            ),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify(song_good)
    else:
        return jsonify([])


@app.route("/api/add-to-playlist", methods=["POST"])
def add_to_playlist():
    """
    This function handles the POST request at the /api/add-to-playlist endpoint.
    It checks if a user session exists. If not, it returns an error message.
    If a user session exists, it retrieves the song data from the request and the user_id from the session.
    It then attempts to add the song to the user's playlist in the MongoDB database.
    If the song is successfully added, it returns a success message.
    If the song already exists in the playlist, it returns an error message.
    If an exception occurs during the process, it returns the error message.
    """

    try:
        # Get song data from request
        song_data = request.get_json()
        if not isinstance(song_data, dict):
            song_data_dict = {
                "name": song_data[0],
                "artists": song_data[1].split(","),
                "release_date": convert_date(song_data[2]),
            }
            song_data = song_data_dict

        # Add user_id to song_data
        song_data["user_id"] = session["user_id"]

        # Check if the song already exists for this user
        existing_song = playlist_collection.find_one(
            {
                "name": song_data["name"],
                "artists": song_data["artists"],
                "release_date": song_data["release_date"],
                "user_id": song_data["user_id"],
            }
        )

        if not existing_song:
            playlist_collection.insert_one(song_data)
            print(f"Added song to playlist: {song_data}")
            return jsonify({"message": "Song added to playlist"})
        else:
            return jsonify({"message": "Song already in playlist"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def convert_date(date_str):
    try:
        # Try parsing the date in the expected format
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT").strftime(
            "%Y-%m-%d"
        )
    except ValueError:
        # If parsing fails, return the original date string
        return date_str


@app.route("/api/get-playlist", methods=["GET"])
def get_playlist():
    """
    This function handles the GET request at the /api/get-playlist endpoint.
    It checks if a user session exists. If not, it returns an empty list.
    If a user session exists, it retrieves the user_id from the session.
    It then retrieves the user's playlist from the MongoDB database.
    It then retrieves the song data from the PostgreSQL database.
    It then returns a JSON list of songs in the user's playlist.
    """

    if "user_id" not in session:
        return jsonify([])  # Return an empty list if there is no user_id in the session

    user_id = session["user_id"]
    songs = playlist_collection.find({"user_id": user_id})
    # Convert MongoDB cursor to list and serialize ObjectId to JSON
    songs_list = []
    for song in songs:
        song["_id"] = str(song["_id"])  # Convert ObjectId to string
        songs_list.append(song)

    print(f"Converted to list: {songs_list}")

    return jsonify(songs_list)


def get_all_playlist_songs_in_postgresql():
    """
    This function retrieves all songs from the user's playlist in MongoDB and checks if they exist in the PostgreSQL database.
    It first checks if the user is logged in by checking if "user_id" is in the session.
    If the user is not logged in, it returns an empty list.
    If the user is logged in, it retrieves the user's playlist from MongoDB and checks each song in the PostgreSQL database.
    It returns a list of all songs in the user's playlist that exist in the PostgreSQL database.
    """
    if "user_id" not in session:
        return jsonify([])  # Return an empty list if there is no user_id in the session

    user_id = session["user_id"]
    songs = playlist_collection.find({"user_id": user_id})

    list_of_songs = []
    for song in songs:
        songs_dict = {
            "name": song["name"],
            "artists": song["artists"],
            "release_date": song["release_date"],
        }
        list_of_songs.append(songs_dict)

    all_songs = []
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            for song in list_of_songs:
                query = """
                SELECT song_id, name, release_date, artists, acousticness, danceability, energy,
                       instrumentalness, liveness, loudness, speechiness, tempo, valence, duration_ms
                FROM songs
                WHERE name = %s AND release_date = %s;
                """
                cursor.execute(query, (song["name"], song["release_date"]))
                songs = cursor.fetchall()

                for song in songs:
                    song_dict = {
                        "song_id": song[0],
                        "name": song[1],
                        "release_date": song[2],
                        "artists": song[3],
                        "acousticness": song[4],
                        "danceability": song[5],
                        "energy": song[6],
                        "instrumentalness": song[7],
                        "liveness": song[8],
                        "loudness": song[9],
                        "speechiness": song[10],
                        "tempo": song[11],
                        "valence": song[12],
                        "duration_ms": song[13],
                    }
                    all_songs.append(song_dict)

            cursor.close()
        finally:
            connection.close()

        return all_songs
    else:
        print("Error in the connection")
        return None


@app.route("/api/delete-from-playlist", methods=["POST"])
def delete_from_playlist():
    """
    This function handles the POST request at the /api/delete-from-playlist endpoint.
    It checks if a user session exists. If not, it returns an error message.
    If a user session exists, it retrieves the song data from the request and the user_id from the session.
    It then attempts to delete the song from the user's playlist in the MongoDB database.
    If the song is successfully deleted, it returns a success message.
    If the song is not found in the playlist, it returns an error message.
    If an exception occurs during the process, it returns the error message.
    """

    if "user_id" not in session:
        return jsonify({"message": "No user session found"}), 400

    try:
        song_data = request.get_json()
        user_id = session["user_id"]

        result = playlist_collection.delete_one(
            {
                "name": song_data["name"],
                "artists": song_data["artists"],
                "release_date": song_data["release_date"],
                "user_id": user_id,
            }
        )

        if result.deleted_count > 0:
            return jsonify({"message": "Song deleted from playlist"})
        else:
            return jsonify({"message": "Song not found in playlist"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/get-taylor-swift-playlist", methods=["GET"])
def get_taylor_swift_playlist():
    """
    This function handles the GET request at the /api/get-taylor-swift-playlist endpoint.
    It connects to the Neo4j database and retrieves all songs from the user's playlist in PostgreSQL.
    It then prints the playlist songs and checks if there are any songs in the playlist.
    If there are songs, it finds songs for the playlist and returns a JSON list of Taylor Swift playlist recommendations.
    If there are no songs, it returns an empty JSON list.
    """
    driver = GraphDatabase.driver(newo4j_uri, auth=(newo4j_user, newo4j_password))
    songs = get_all_playlist_songs_in_postgresql()
    print("\nPlaylist songs:\n", songs)
    if songs:
        tswift_playlist_recommendations_raw = find_songs_for_playlist(driver, songs, 3)
        tswift_playlist_recommendations = [
            {"name": record["name"]} for record in tswift_playlist_recommendations_raw
        ]
        print("\nTaylor Playlist Recommendations:\n", tswift_playlist_recommendations)
        return jsonify(tswift_playlist_recommendations)
    else:
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")
