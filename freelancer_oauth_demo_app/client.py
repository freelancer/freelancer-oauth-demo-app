import json
import os

from flask import (
    Flask,
    url_for,
    session,
    request,
    jsonify,
    redirect,
    render_template,
    Markup,
)
from flask_login import current_user
from flask_oauthlib.client import OAuth
import flask
import flask_login
import requests

from config import CONFIG

# client and user should be added prior testing
OAUTH_BASE_URL = "{server_base_url}/oauth/".format(**CONFIG)
API_BASE_URL = "{server_base_url}/api/v1/".format(**CONFIG)

app = Flask(
    __name__, template_folder="templates", static_folder="static", static_url_path=""
)
app.debug = True
app.secret_key = "secret"
oauth = OAuth(app)

login_manager = flask_login.LoginManager()
login_manager.login_view = "handle_login"
login_manager.init_app(app)

remote = oauth.remote_app(
    CONFIG["server_base_url"],
    consumer_key=CONFIG["client_id"],
    consumer_secret=CONFIG["client_secret"],
    base_url=CONFIG["server_base_url"],
    access_token_url="{}/token".format(OAUTH_BASE_URL),
    authorize_url="{}/authorise".format(OAUTH_BASE_URL),
)

###############################################################################
#                                                                             #
#                         Our User Representation                             #
#                                                                             #
###############################################################################


USER_CACHE = {}


class User(flask_login.UserMixin):
    def __init__(self, freelancer_info, access_token):
        self.info = freelancer_info
        self.id = freelancer_info["id"]
        USER_CACHE[self.id] = self
        self.token = access_token


@login_manager.user_loader
def user_loader(user_id):
    return USER_CACHE.get(int(user_id))


###############################################################################
#                                                                             #
#                             Helper functions                                #
#                                                                             #
###############################################################################


def get_freelancer_user_info(user_id=None):
    headers = {"Freelancer-OAuth-V1": "{}".format(session["access_token"][0])}
    freelancer_api_host = "https://www.freelancer-sandbox.com/api"
    api_url = "{}/users/0.1/self".format(freelancer_api_host)
    res = requests.get(api_url, headers=headers, verify=False)
    if res.status_code == 200:
        return res.json()["result"]
    return None


def login_redir():
    redir = request.args.get("next")
    if redir:
        redir = unquote(request.args.get("next"))

    if redir and not is_valid_redir(redir):
        flask.abort(500, "Invalid redirect uri")

    return flask.redirect(redir or flask.url_for("index"))


###############################################################################
#                                                                             #
#                     Endpoints to manage OAuth State                         #
#                                                                             #
###############################################################################


@app.route("/")
@flask_login.login_required
def index():
    """
    Home page of your application
    """
    if "access_token" in session:
        freelancer_user_info = current_user.info
        client_info = {"client_name": CONFIG["client_name"]}
        if freelancer_user_info and client_info:
            page_data = dict()
            page_data.update(freelancer_user_info)
            page_data.update(client_info)
            return render_template("/home.html", **page_data)
        else:
            return handle_logout()
    return handle_logout()


@app.route("/login", methods=["GET", "POST"])
def handle_login():
    """Logs in a user using OAuth.

    The user will be prompted to log into accounts.freelancer-sandbox.com and
    pass an OAuth Grant Token to your server (to be received below in '/authorized')
    """
    if current_user.is_authenticated:
        return login_redir()

    if request.method == "GET":
        client_info = {"client_name": CONFIG["client_name"]}
        return render_template(
            "/login.html", error=request.args.get("error"), **client_info
        )

    prompt = "select_account"
    advanced_scopes = "1 6"
    return remote.authorize(
        callback=CONFIG["client_redirect"],
        prompt=prompt,
        advanced_scopes=advanced_scopes,
        scope="basic",
    )


# This function route is to be set to whatever your client redirect uri is.
# For example, http://www.yourhost.com/authorized, then this route should be '/authorized'
@app.route("/authorized")
def authorized():
    """
    Receives an OAuth Grant Token, to be passed to accounts.freelancer-sandbox.com to be validated
    and exchanged for an OAuth Access Token
    """
    if request.args.get("error"):
        return "Error occurred: {}".format(request.args.get("error"))

    resp = remote.authorized_response()
    if resp is None:
        return "Access denied: reason={} error={}".format(
            request.args["error_reason"], request.args["error_description"]
        )
    session["access_token"] = (resp["access_token"],)
    session["refresh_token"] = (resp["refresh_token"],)

    freelancer_user_info = get_freelancer_user_info()
    if freelancer_user_info:
        user = User(freelancer_user_info, resp["access_token"])
        flask_login.login_user(user)
    else:
        handle_logout()
        return redirect(url_for("login"))
    return redirect(url_for("index"))


@app.route("/logout")
@flask_login.login_required
def handle_logout(error=None):
    """Logs a user out and removes their access token locally."""
    clear_token()
    resp = flask.redirect(flask.url_for("index", error=error))
    flask_login.logout_user()
    return resp


@app.route("/clear")
def clear_token():
    """Removes the current OAuth access token locally."""
    session.pop("access_token", None)
    session.pop("refresh_token", None)
    return redirect(url_for("index"))


@app.route("/revoke")
def revoke_token():
    """Revokes the current OAuth access token both locally and on the remote host."""
    if "access_token" in session:
        data = {"token_type_hint": "access_token", "token": session["access_token"]}
        url = "{server_base_url}revoke".format(**CONFIG)
        resp = remote.post(url=url, data=data)
        if resp.status == 200:
            clear_token()
            return redirect(url_for("index"))
        else:
            message = "Error"
            if resp.data.get("message"):
                message += ": " + resp.data["message"]
            return message

    return "No token to revoke"


@app.route("/refresh")
def refresh_token():
    """Uses the current refresh token to get a new OAuth access token. 

    This will return a new OAuth access token for the same user the OAuth
    access and refresh token were previously generated for.
    """
    if "refresh_token" in session:
        args = ("basic", session.get("refresh_token")[0], CONFIG["client_id"])
        url = (
            "token?grant_type=refresh_token"
            "&scope={scope}&refresh_token={refresh_token}&client_id={client_id}"
        ).format(
            scope="basic",
            refresh_token=session.get("refresh_token")[0],
            client_id=CONFIG["client_id"],
        )
        resp = remote.get(url)
        if resp.status == 200:
            session["access_token"] = (resp.data["access_token"],)
            session["refresh_token"] = (resp.data["refresh_token"],)
            current_user.token = resp.data["access_token"]
        # if fail to refresh token, clear bearer token
        else:
            return clear_token()
    else:
        return clear_token()
    return redirect(url_for("index"))


@app.route("/client_credentials")
def client_credentials_grant():
    """
    'client_credentials' grant type
    property can get access token with client credentials
    """
    url = (
        "{server_base_url}token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
    ).format(**CONFIG)

    resp, content = remote.http_request(uri=url, method="GET")

    if resp.status == 200:
        data = json.loads(content.decode("utf-8"))
        session["access_token"] = (data["access_token"],)

    return redirect(url_for("index"))


@app.route("/project", methods=["GET", "POST"])
@flask_login.login_required
def handle_createapp():
    template_var = {}
    if request.method == "POST":
        try:
            client_vals = request.form.to_dict()
            service = client_vals["service"]
            location = client_vals["location"]
            budget = client_vals["budget"]
            if not budget.isnumeric() or int(budget) < 1:
                raise Exception("Budget must be a positive number")
            budget = int(budget)
            token = current_user.token
            headers = {"Freelancer-OAuth-V1": token, "Content-Type": "application/json"}
            body = {
                "title": "Looking for service: {}".format(service),
                "description": "I am looking for {} at location {}. My budget is {}".format(
                    service, location, budget
                ),
                "currency": {"id": 1},
                "budget": {"minimum": budget, "maximum": budget, "currency_id": 1},
                "jobs": [{"id": 632}],
                "type": "FIXED",
            }
            r = requests.post(
                "https://www.freelancer-sandbox.com/api/projects/0.1/projects/",
                data=json.dumps(body),
                headers=headers,
            )
            if not r.status_code == 200:
                json_response = r.json()
                if json_response:
                    template_var["message"] = Markup(json_response["message"])
                else:
                    template_var["message"] = Markup(r.text)
            else:
                project_id = r.json()["result"]["id"]
                template_var["message"] = Markup(
                    'Project posted! View your project <a href="https://www.freelancer-sandbox.com/projects/{}".format(project_id)">here</a>'.format(
                        project_id
                    )
                )
            return render_template("/project.html", **template_var)
        except Exception as e:
            template_var["message"] = e.message
    return render_template("/project.html", **template_var)


###############################################################################
#                                                                             #
#                          JSON data set endpoints                            #
#                                                                             #
###############################################################################


@app.route("/my_token")
def return_token():
    if "access_token" in session:
        return jsonify({"access_token": session.get("access_token")[0]})

    return redirect(url_for("index"))


@app.route("/explain_token_scope/", methods=["GET"], defaults={"access_token": None})
@app.route("/explain_token_scope/<access_token>")
def explain_token_scope(access_token):
    if "access_token" in session:
        resp = remote.get(
            "{}user/scope/{}".format(API_BASE_URL, session.get("access_token")[0])
        )
        return jsonify(resp.data)

    return redirect(url_for("index"))


@app.route("/user")
def user_get():
    """Returns a JSONic representation of the current user.

    The current user is determined from the session OAuth access token
    """
    if "access_token" in session:
        url = "{}user".format(API_BASE_URL)
        resp = remote.get(url=url)
        if resp.status == 200:
            return jsonify(resp.data)
        else:
            return jsonify(resp.data)
    else:
        return redirect(url_for("index"))


# User by remote.get by oauthlib
@remote.tokengetter
def get_oauth_token():
    return session.get("access_token")


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
    app.run(host="127.0.0.1", port=8080)
