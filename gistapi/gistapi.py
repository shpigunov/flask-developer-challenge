# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import re
import requests
from requests.exceptions import ConnectionError
from flask import Flask, jsonify, request


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
        username=username)

    try:
        response = requests.get(gists_url)
    except ConnectionError:
        return {"message": "Connection Error"}

    # BONUS: What failures could happen?
    if not response.ok:
        return {"message": "Invalid Response from Github"}

    # BONUS: Paging? How does this work for users with tons of gists?

    return response.json()


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # DONE: Validate the arguments?
    if not 'username' in post_data:
        return jsonify({
            "status":  "user_not_specified"
        })

    if not 'pattern' in post_data:
        return jsonify({
            "status":  "pattern_not_specified"
        })

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)

    # DONE: Handle invalid users?
    if 'message' in gists:
        if gists['message'] == 'Not Found':
            return jsonify({
                "status":  "user_not_found",
            })
        if gists['message'] == 'Connection Error':
            return jsonify({
                "status":  "github_connection_error",
            })

    gist_data = {}
    matches = []

    for gist in gists:
        # DONE: Fetch each gist and check for the pattern
        # BONUS: What about huge gists?
        # BONUS: Can we cache results in a datastore/db?

        # All the file urls in the gist
        for file in gist['files'].values():
            raw_url = file['raw_url']
            with requests.get(raw_url) as r:
                if r.ok:
                    re_matches = re.search(pattern, r.text)
                    if re_matches:
                        base, gist_id = gist['html_url'].rsplit('/', 1)
                        matches.append(f'{base}/{username}/{gist_id}')
                    else:
                        pass

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matches

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
