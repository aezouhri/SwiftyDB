/**
 * Event listener for the 'db-search-btn' button.
 * When the button is clicked, it retrieves the song name and artist name from the input fields,
 * and calls the searchSongs function with these values and 'db' as the source.
 */
document.getElementById("db-search-btn").addEventListener("click", function () {
    let songName = document.getElementById("db-song-search").value || "";
    let artistName = document.getElementById("db-artist-search").value || "";
    searchSongs(songName, artistName, "db");
});

/**
 * Event listener for the 'spotify-search-btn' button.
 * When the button is clicked, it retrieves the song name and artist name from the input fields,
 * and calls the searchSongs function with these values and 'spotify' as the source.
 */

document
    .getElementById("spotify-search-btn")
    .addEventListener("click", function () {
        let songName = document.getElementById("spotify-song-search").value || "";
        let artistName =
            document.getElementById("spotify-artist-search").value || "";
        searchSongs(songName, artistName, "spotify");
    });

/**
 * Event listener for the 'taylor-swift-playlist-btn' button.
 * When the button is clicked, it calls the getTaylorSwiftPlaylistRecommendations function.
 */
document
    .getElementById("taylor-swift-playlist-btn")
    .addEventListener("click", function () {
        getTaylorSwiftPlaylistRecommendations();
    });

/**
 * Function to search songs from a specified source.
 *
 * @param {string} songName - The name of the song to search.
 * @param {string} artistName - The name of the artist to search.
 * @param {string} source - The source to search from. Can be 'spotify' or 'db'.
 */

function searchSongs(songName, artistName, source) {
    const endpoint =
        source === "spotify" ? "/api/search-spotify" : "/api/search-songs";
    const resultsContainerId =
        source === "spotify" ? "spotify-search-results" : "db-search-results";

    fetch(
        `${endpoint}?song=${encodeURIComponent(
            songName
        )}&artist=${encodeURIComponent(artistName)}`
    )
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then((songs) => {
            const resultsContainer = document.getElementById(resultsContainerId);
            resultsContainer.innerHTML = "";
            songs.forEach((song, index) => {
                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.id = source + "_song_" + index;
                checkbox.value = JSON.stringify(song);

                const label = document.createElement("label");
                label.htmlFor = source + "_song_" + index;
                // Handle artist names depending on the source
                let artistText =
                    source === "spotify" ? song.artists.join(", ") : song[1];
                label.textContent = `${song.name ? song.name : song[0]
                    } by ${artistText}`;

                const div = document.createElement("div");
                div.appendChild(checkbox);
                div.appendChild(label);
                resultsContainer.appendChild(div);
            });
            document.getElementById(
                source + "-search-results-container"
            ).style.display = "block";
        })
        .catch((error) => console.error("Error:", error));
}

document
    .getElementById("add-to-playlist-btn")
    .addEventListener("click", function () {
        const checkboxes = document.querySelectorAll(
            '#db-search-results input[type="checkbox"]:checked, #spotify-search-results input[type="checkbox"]:checked'
        );
        let addSongPromises = [];

        checkboxes.forEach((checkbox) => {
            const song = JSON.parse(checkbox.value);
            console.log("Adding song to playlist: ", song);
            addSongPromises.push(addSongToPlaylist(song));
            checkbox.checked = false;
        });

        Promise.all(addSongPromises)
            .then(() => {
                loadPlaylist();
                document.getElementById("playlist-status").textContent =
                    "Songs added to playlist!";
            })
            .catch((error) => console.error("Error:", error));
    });

/**
 * Adds a song to the playlist.
 *
 * @param {Object} song - The song to be added to the playlist.
 * @returns {Promise} A promise that resolves to the response of the fetch request.
 */

function addSongToPlaylist(song) {
    return fetch("/api/add-to-playlist", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(song),
    }).then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    });
}

document
    .getElementById("get-taylor-swift-recommendations")
    .addEventListener("click", function () {
        const selectedOption =
            document.getElementById("song-select").options[
            document.getElementById("song-select").selectedIndex
            ];
        const selectedSong = JSON.parse(selectedOption.value);
        getTaylorSwiftRecommendations(selectedSong);
    });

/**
 * Fetches Taylor Swift song recommendations based on the selected song.
 *
 * @param {Object} song - The selected song based on which recommendations are to be fetched.
 */
function getTaylorSwiftRecommendations(song) {
    fetch("http://127.0.0.1:5002/api/taylor-swift-recommendations", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(song),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log("Top 3 Taylor Swift songs that match your selection:");
            data.forEach((rec, index) => {
                console.log(`${index + 1}. ${rec[0]}`);
            });

            // Create a new list element for each recommendation and append it to the #recommendations element
            const recommendationsElement =
                document.getElementById("results-container");
            recommendationsElement.innerHTML = ""; // Clear previous recommendations
            data.forEach((rec, index) => {
                const listItem = document.createElement("li");
                listItem.textContent = `${index + 1}. ${rec[0]}`;
                recommendationsElement.appendChild(listItem);
            });
        })
        .catch((error) => console.error("Error:", error));
}

/**
 * Loads the user's playlist from the server and displays it in the #playlist element.
 * Each song is displayed with a checkbox and a label containing the song name and artist(s).
 * The value of each checkbox is the JSON string representation of the song object.
 */

function loadPlaylist() {
    fetch("/api/get-playlist")
        .then((response) => response.json())
        .then((songs) => {
            const playlistElement = document.getElementById("playlist");
            playlistElement.innerHTML = ""; // Clear current playlist
            songs.forEach((song, index) => {
                const listItem = document.createElement("li");

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.id = "playlist_song_" + index;
                checkbox.value = JSON.stringify(song);

                const label = document.createElement("label");
                label.htmlFor = "playlist_song_" + index;
                label.textContent = `${song.name} by ${song.artists.join(", ")}`;

                listItem.appendChild(checkbox);
                listItem.appendChild(label);
                playlistElement.appendChild(listItem);
            });
        })
        .catch((error) => console.error("Error:", error));
}

/**
 * Event listener for the 'delete-from-playlist-btn' button.
 * When the button is clicked, it retrieves all checked checkboxes from the playlist,
 * parses the associated song data, and calls the deleteSongFromPlaylist function for each song.
 */

document
    .getElementById("delete-from-playlist-btn")
    .addEventListener("click", function () {
        const checkboxes = document.querySelectorAll(
            '#playlist input[type="checkbox"]:checked'
        );
        checkboxes.forEach((checkbox) => {
            const song = JSON.parse(checkbox.value);
            deleteSongFromPlaylist(song);
        });
    });

/**
 * Deletes a song from the playlist.
 *
 * @param {Object} song - The song to be deleted from the playlist.
 */
function deleteSongFromPlaylist(song) {
    fetch("/api/delete-from-playlist", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(song),
    })
        .then((response) => response.json())
        .then((data) => {
            loadPlaylist(); // Reload playlist after deletion
            console.log(data.message); // Log response message
        })
        .catch((error) => console.error("Error:", error));
}

/**
 * Fetches Taylor Swift playlist recommendations from the server.
 * Sends a GET request to the '/api/get-taylor-swift-playlist' endpoint.
 * Displays the songs in the 'taylor-swift-playlist-container' element.
 */
function getTaylorSwiftPlaylistRecommendations() {
    fetch("/api/get-taylor-swift-playlist")
        .then((response) => response.json())
        .then((songs) => {
            let container = document.getElementById(
                "taylor-swift-playlist-container"
            );
            container.innerHTML = ""; // Clear existing content
            songs.forEach((song) => {
                let songElement = document.createElement("div");
                songElement.innerHTML = `
                <input type="checkbox" id="song-${song.name}" name="song" value="${song.name}">
                <label for="song-${song.name}">${song.name}</label>
            `;
                container.appendChild(songElement);
            });
        })
        .catch((error) => console.error("Error:", error));
}

/**
 * Event listener for the 'get-taylor-swift-playlist-recommendations' button.
 * When the button is clicked, it triggers the getTaylorSwiftPlaylistRecommendations function.
 */

document
    .getElementById("get-taylor-swift-playlist-recommendations")
    .addEventListener("click", getTaylorSwiftPlaylistRecommendations);

/**
 * Event listener for the 'add-spotify-song-btn' button.
 * When the button is clicked, it triggers a function that adds selected songs from Spotify to the playlist.
 * It fetches all checked checkboxes within the 'spotify-search-results' element.
 * For each checked checkbox, it parses the song data from the checkbox value and adds the song to the playlist.
 * After adding the song, it unchecks the checkbox.
 */
document
    .getElementById("add-spotify-song-btn")
    .addEventListener("click", function () {
        const checkboxes = document.querySelectorAll(
            '#spotify-search-results input[type="checkbox"]:checked'
        );
        let addSongPromises = [];

        checkboxes.forEach((checkbox) => {
            const song = JSON.parse(checkbox.value);
            addSongPromises.push(addSongFromSpotify(song));
            checkbox.checked = false;
        });
    });

/**
 * Adds a song from Spotify to the PostgreSQL database.
 * Sends a POST request to the '/api/add-spotify-song' endpoint with the song data in the request body.
 * @param {Object} song - The song object to be added to the database.
 */
function addSongFromSpotify(song) {
    fetch("api/add-spotify-song", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(song),
    })
        .then((response) => response.json())
        .then((data) => {
            // Song added to database
            // You can update the UI here if needed
        })
        .catch((error) => console.error("Error:", error));
}
