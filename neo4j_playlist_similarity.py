from neo4j import GraphDatabase
from sklearn.cluster import KMeans
import numpy as np


def send_song_to_neo4j_and_get_similar(driver, song_features):
    # Adjust the Cypher query for GDS
    query = """
    WITH $new_song_features AS new_song_features
    MATCH (song:Song)
    WITH song, new_song_features, 
         [song.acousticness, song.danceability, song.energy, song.instrumentalness, song.liveness, song.loudness, song.speechiness, song.tempo, song.valence] AS song_features
    WITH song, gds.similarity.cosine(new_song_features, song_features) AS similarity
    RETURN song.name AS name, similarity
    ORDER BY similarity DESC
    LIMIT 1
    """

    # Execute the query
    with driver.session() as session:
        result = session.run(query, new_song_features=song_features)
        records = [record for record in result]
        return records


def cluster_songs(song_features, num_clusters=3):
    # Cluster the songs
    kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(song_features)
    centroids = kmeans.cluster_centers_
    return centroids


def get_playlist_songs_features(playlist_songs: list[dict]):
    # Retrieve or compute the feature vectors for each song in the playlist
    song_features = []
    for new_song in playlist_songs:
        features = [
            new_song['acousticness'],
            new_song['danceability'],
            new_song['energy'],
            new_song['instrumentalness'],
            new_song['liveness'],
            new_song['loudness'],
            new_song['speechiness'],
            new_song['tempo'],
            new_song['valence'],
        ]
        song_features.append(features)
    return song_features


def find_songs_for_playlist(driver, playlist_songs: list[dict], n: int):
    # Get features of playlist songs
    features = get_playlist_songs_features(playlist_songs)

    # Perform clustering
    centroids = cluster_songs(np.array(features), n)

    # Find similar songs for each centroid
    recommended_songs = []
    for centroid in centroids:
        similar_songs = send_song_to_neo4j_and_get_similar(driver, centroid)
        recommended_songs.extend(similar_songs)

    return recommended_songs


if __name__ == "__main__":
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "swiftydb"

    driver = GraphDatabase.driver(uri, auth=(user, password))

    new_song = {
        "acousticness": 0.0102,
        "danceability": 0.909,
        "energy": 0.815,
        "instrumentalness": 7.31e-05,
        "liveness": 0.225,
        "loudness": -4.72,
        "speechiness": 0.251,
        "tempo": 91.979,
        "valence": 0.49,
    }
    # similar_songs = send_song_to_neo4j_and_get_similar(driver, new_song)
    #
    # for record in similar_songs:
        # print(record["name"], record["similarity"])


    playlist_songs_example = [
        {
            "acousticness": 0.0102,
            "danceability": 0.909,
            "energy": 0.815,
            "instrumentalness": 7.31e-05,
            "liveness": 0.225,
            "loudness": -4.72,
            "speechiness": 0.251,
            "tempo": 91.979,
            "valence": 0.49,
        },
        {
            "acousticness": 0.0000,
            "danceability": 0.4510,
            "energy": 0.7100,
            "instrumentalness": 0.0891,
            "liveness": 0.0985,
            "loudness": - 5.739,
            "speechiness": 0.0399,
            "tempo": 145.703,
            "valence": 0.3150,
        },
        {
            "acousticness": 0.7750,
            "danceability": 0.2830,
            "energy": 0.2230,
            "instrumentalness": 0.0000,
            "liveness": 0.1260,
            "loudness": -11.686,
            "speechiness": 0.0296,
            "tempo": 83.555,
            "valence": 0.2480,
        },
        {
            "acousticness": 0.0895,
            "danceability": 0.3740,
            "energy": 0.9050,
            "instrumentalness": 0.0000,
            "liveness": 0.0759,
            "loudness": -5.748,
            "speechiness": 0.1700,
            "tempo": 184.682,
            "valence": 0.7780,
        },
    ]

    recomendations = find_songs_for_playlist(driver, playlist_songs_example, 3)
    print(recomendations)


    driver.close()
