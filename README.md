# SwiftyDB - A Data-Driven Delight for Taylor Swift Fans

In an era where Taylor Swift reigns supreme as the queen of hearts and charts, we've concocted a system that's nothing short of Swiftacular! Imagine a world where you can dive deeper than ever into the Swiftverse, analyzing every beat, lyric, and hidden Easter egg planted by the pop icon herself. Our project is a data-driven delight, tailor-made for the 99.9999% of female youth who would proudly declare their allegiance to TayTay in a heartbeat. Whether you're a casual listener or a Swiftie so dedicated you've considered naming your cat Meredith, our system offers a unique way to engage with the work of your favorite artist. So, grab your glittery guitar, don your best cardigan, and get ready to embark on a statistical journey through Taylor Swift's musical masterpiece!

# Server Side overview

server.py is a Flask web application that provides various endpoints for searching and managing songs and playlists. It integrates with Spotify's API to search for songs and retrieve audio features, uses a PostgreSQL database to store song data, and MongoDB to manage user playlists. Additionally, it connects to a Neo4j graph database for playlist recommendations.

## Dependencies
- Flask
- Flask-CORS
- psycopg2
- requests
- base64
- pymongo
- neo4j
- config module (custom)

## Configuration
- Spotify API credentials are required (CLIENT_ID and CLIENT_SECRET).
- MongoDB connection string for the MDB_Project database.
- Neo4j database connection details.

## Endpoints
GET /
Renders the main index page. If no user_id is in the session, it generates a new one.

GET /search-songs
Renders the song search page.

GET /api/search-songs
Searches for songs in the PostgreSQL database by name and artist. Returns a JSON list of songs.


POST /api/taylor-swift-recommendations
Recommends Taylor Swift songs based on acoustic features from the PostgreSQL database. Returns a JSON list of recommendations.

GET /api/search-spotify
Searches for songs on Spotify by name and artist. Returns a JSON list of songs with their Spotify IDs and other metadata.

POST /api/add-spotify-song
Adds a song from Spotify to the PostgreSQL database, including its audio features.

POST /api/add-to-playlist
Adds a song to the user's playlist in MongoDB. Checks for duplicates before adding.

GET /api/get-playlist
Retrieves the user's playlist from MongoDB and returns it as a JSON list.

GET /api/get-taylor-swift-playlist
Generates or fetches Taylor Swift playlist recommendations from the Neo4j database. Returns a JSON list of recommendations.

POST /api/delete-from-playlist
Deletes a song from the user's playlist in MongoDB.

## Helper Functions
credentials()
Reads database credentials from a file.

create_connection()
Creates a connection to the PostgreSQL database.

get_spotify_token()
Retrieves an access token from Spotify.

convert_date(date_str)
Converts a date string to a specific format.

get_all_playlist_songs_in_postgresql()
Retrieves all songs from the user's playlist in MongoDB and checks if they exist in the PostgreSQL database.

## Running the Application
The application is configured to run on localhost with port 5002 in debug mode.

Run `python server.py` to start the application.

# Client Side overview

search_songs.js is a JavaScript file that provides functionality for searching songs, managing playlists, and interacting with the server-side API endpoints. It uses the Fetch API to make HTTP requests to the server.

## Functions

searchSongs(songName, artistName, source)
This function searches for songs either from Spotify or the PostgreSQL database, depending on the source parameter. It sends a GET request to the appropriate endpoint with the song name and artist name as query parameters. The results are then displayed in the appropriate results container.

addSongToPlaylist(song)
This function adds a song to the user's playlist. It sends a POST request to the /api/add-to-playlist endpoint with the song data in the request body.

getTaylorSwiftRecommendations(song)
This function gets Taylor Swift song recommendations based on the acoustic features of a selected song. It sends a POST request to the /api/taylor-swift-recommendations endpoint with the selected song data in the request body. The recommendations are then displayed in the #results-container element.

loadPlaylist()
This function loads the user's playlist from the server. It sends a GET request to the /api/get-playlist endpoint and displays the songs in the #playlist element.

deleteSongFromPlaylist(song)
This function deletes a song from the user's playlist. It sends a POST request to the /api/delete-from-playlist endpoint with the song data in the request body. The playlist is then reloaded to reflect the changes.

getTaylorSwiftPlaylistRecommendations()
This function gets Taylor Swift playlist recommendations from the server. It sends a GET request to the /api/get-taylor-swift-playlist endpoint and displays the songs in the #taylor-swift-playlist-container element.

addSongFromSpotify(song)
This function adds a song from Spotify to the PostgreSQL database. It sends a POST request to the /api/add-spotify-song endpoint with the song data in the request body.

## Event Listeners
The script also sets up several event listeners for button clicks, which trigger the above functions with the appropriate parameters. For example, the 'Add to Playlist' button triggers the addSongToPlaylist function for each selected song.