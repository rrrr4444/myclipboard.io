from flask import Flask, json, render_template, make_response, jsonify, url_for, flash, request, session
from werkzeug.utils import redirect
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import os


import api


app = Flask(__name__)
cors = CORS(app, resources={"/api/*": {"origins": "*"}})
app.secret_key = os.environ.get("APP_SECRET_KEY")
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per minute"]
)


@app.context_processor
def dark_mode():
    """
    Create dark mode functionality.
    """
    dark_mode = request.cookies.get("darkMode")
    if dark_mode == "true":
        background = "dark"
        accent = "light"
        dark_mode = True
    else:
        background = "light"
        accent = "dark"
        dark_mode = False

    return {"background": background,
            "accent": accent,
            "dark_mode": dark_mode
            }


@app.route("/")
def index():
    """
    Homepage shows clipboard.
    """
    email = session.get("email")

    if not email:
        return redirect(url_for("email"))

    elif not api.user_exists(email):
        # If account deleted, clear session
        session.clear()
        return redirect(url_for("email"))
    else:
        # Logged in user
        clipboard = api.read(email)
        return render_template("index.html", clipboard=clipboard)


@app.route("/about/")
def about():
    """
    About service.
    """
    return render_template("about.html")


@app.route("/download/")
def download():
    """
    Download links for apps.
    """
    return render_template("download.html")


@app.route("/privacy/")
def privacy():
    """
    Privacy policy.
    """
    return render_template("privacy.html")


@app.route("/terms/")
def terms():
    """
    Terms and conditions.
    """
    return render_template("terms.html")


@app.route("/email/", methods=["GET", "POST"])
def email():
    """
    Redirect from email form
    to login or regiser
    """
    # Handle oauth
    if request.method == "GET":
        oauth_client = request.args.get("oauth")

    elif request.method == "POST":
        oauth_client = request.form.get("oauth")

    redirect_after = request.args.get("redirect_after")

    # Create query string for oauth redirects
    if oauth_client:
        query_string = f"?oauth={oauth_client}"
    else:
        query_string = ""

    if request.method == "POST":
        email = request.form.get("email")
        if redirect_after:
            resp = make_response(redirect(url_for(redirect_after)))
            resp.set_cookie("email", email, max_age=(60 * 10))
            return resp
        return login_redirect(email, query_string)

    elif request.method == "GET":
        email = session.get("email")
        if email and not oauth_client:
            # Redirect to index if not in oauth flow
            return redirect(url_for("index"))
        elif email and oauth_client:
            # Redirect to login page if in oauth flow
            return login_redirect(email, query_string)
        return render_template("email.html", oauth_client=oauth_client, redirect_after=redirect_after)


def login_redirect(email, query_string):
    """
    Return a redirect object for the login or register form
    """

    if api.user_exists(email):
        form = "login"
    else:
        form = "register"

    resp = make_response(redirect(url_for(form) + query_string))
    resp.set_cookie("email", email, max_age=(60 * 10))
    return resp


@app.route("/email/verify/")
def verify_email():
    """
    Handle verify email link.
    """
    email = request.args.get("email")
    token = request.args.get("token")
    if api.validate_email_token(email, token):
        # Log in user
        session["email"] = email
        flash(f"Email confirmed!", "success")
        return redirect(url_for("index"))

    elif api.email_confirmed(email):
        flash("Email already confirmed.", "danger")
        return redirect(url_for("index"))
    else:
        flash("Invalid confirmation link", "danger")
        return redirect(url_for("login"))


@app.route("/login/", methods=["GET", "POST"])
# @limiter.limit("200 per day, 50 per hour, 10 per minute")
def login():
    """
    Login user.
    """
    # Handle oauth
    if request.method == "GET":
        oauth_client = request.args.get("oauth")
    elif request.method == "POST":
        oauth_client = request.form.get("oauth")

    # Create query string for oauth redirects
    if oauth_client:
        query_string = f"?oauth={oauth_client}"
    else:
        query_string = ""

    cookie_email = request.cookies.get("email")
    session_email = session.get("email")

    if cookie_email:
        email = cookie_email
    else:
        email = session_email

    if not email:
        flash("Session Expired", "primary")
        return redirect(url_for("email") + query_string)

    if request.method == "POST":

        password = request.form.get("password")

        if not api.email_confirmed(email):
            flash("See link in email to confirm account.", "warning")
            # Resend email to allow for a retry
            api.send_confirm_email(email)
            return redirect(url_for("login"))

        if api.verify_login(email, password):
            session["email"] = email
            session.permanent = True

            # Handle oauth
            if oauth_client:
                return redirect("/token/" + oauth_client + "/")

            return redirect(url_for("index"))

        flash("Invalid Password", "danger")
        return redirect(url_for("login") + query_string)

    elif request.method == "GET":
        if session.get("email") and not oauth_client:
            # Don't redirect in oauth flow
            return redirect(url_for("index"))
        if session.get("email") and oauth_client:
            # Redirect to getting token if signed in
            return redirect("/token/" + oauth_client + "/")
        return render_template("login.html", oauth_client=oauth_client)


@app.route("/register/", methods=["GET", "POST"])
# @limiter.limit("100 per day, 20 per hour, 10 per minute")
def register():
    """
    Register user.
    """
    # If can't find email cookie, go back to email
    email = request.cookies.get("email")
    if not email:
        return redirect(url_for("email"))

    # Handle oauth
    if request.method == "GET":
        oauth_client = request.args.get("oauth")
    elif request.method == "POST":
        oauth_client = request.form.get("oauth")

    # Create query string for oauth redirects
    if oauth_client:
        query_string = f"?oauth={oauth_client}"
    else:
        query_string = ""

    if request.method == "POST":

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if api.user_exists(email):
            flash("Email already registered.", "danger")
            return redirect(url_for("login"))

        if password != confirmation:
            flash("Passwords Don't Match.", "warning")
            return redirect(url_for("register") + query_string)

        password_length = len(password)

        if password_length < 8:
            flash("Passwords must be at least 8 characters.", "warning")
            return redirect(url_for("register") + query_string)

        elif password_length > 512:
            flash("Passwords must be 512 or less characters.", "warning")
            return redirect(url_for("register") + query_string)

        api.register(email, password)

        api.send_confirm_email(email)
        return render_template("check_email_confirm.html")

    elif request.method == "GET":
        if session.get("email"):
            return redirect(url_for("index"))
        return render_template("register.html", oauth_client=oauth_client)


@app.route("/token/<oauth_client>/")
def token(oauth_client):
    """
    Handle oauth token response.
    """
    email = session.get("email")
    if not email:
        # Not logged in
        return redirect(url_for("email"))
    if oauth_client == "chrome":
        token = api.get_token(email)
        return redirect(f"chrome-extension://emhmaepmgpjnimnogbehplipclejinpa/templates/authenticate.html?token={token}&email={email}")
    elif oauth_client == "mobile":
        {"token": "token"}
        return jsonify(token)
    else:
        return "Error: invalid oauth client.", 400


@app.route("/account/")
def account():
    """
    Change account settings.
    """
    email = session.get("email")
    if not api.user_exists(email):
        session.clear()
        return redirect(url_for("email"))
    email = session.get("email")
    return render_template("account.html", email=email)


@app.route("/account/password/", methods=["GET", "POST"])
def update_password():
    """
    Change account settings.
    """
    if request.method == "POST":
        email = session.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if password != confirmation:
            flash("Passwords don't match", "warning")
            return redirect(url_for("account"))

        if len(password) < 8:
            flash("Enter at least 8 characters", "warning")
            return redirect(url_for("account"))

        api.update_password(email, password)
        flash("Password changed", "success")

    return redirect(url_for("account"))


@app.route("/account/delete/", methods=["GET", "POST"])
def delete_account():
    """
    Delete Account.
    """
    if request.method == "POST":
        email = session.get("email")

        if not email:
            return redirect(url_for("email"))

        api.delete_account(email)
        session.clear()
        return render_template("account_deleted.html")

    return redirect(url_for("index"))


@app.route("/forgot/")
def forgot():
    """
    Reset password with reset link.
    """
    if session.get("email"):
        return redirect(url_for("account"))

    email = request.cookies.get("email")

    if not email:
        flash("Enter your email", "primary")
        return redirect(f"{url_for('email')}?redirect_after=forgot")

    if not api.user_exists(email):
        flash(f"{email.lower()} not registered.", "danger")
        return url_for("forgot")

    api.send_password_reset(email)
    flash(f"Reset link sent to {email}", "primary")
    return redirect(url_for("check_email_reset"))


@app.route("/forgot/check_email/")
def check_email_reset():
    return render_template("check_email_reset.html")


@app.route("/forgot/reset/")
def reset_password():
    """
    Reset password with reset link.
    """
    email = request.args.get("email")
    token = request.args.get("token")

    if api.validate_reset_token(email, token):
        session["email"] = email
        flash(f"You may now change your password.", "primary")
        return redirect(url_for("account"))
    else:
        flash("Reset link expired", "danger")
        return redirect(url_for("login"))


@app.route("/logout/")
def logout():
    """
    Logout user.
    """
    session.clear()
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("email", "", max_age=1)
    resp.set_cookie("darkMode", "false", max_age=1)
    flash("Logged Out", "success")
    return resp


@app.route("/set/", methods=["GET", "POST"])
def set():
    """
    Set new value for clipboard.
    """
    email = session.get("email")

    if not api.user_exists(email):
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        contents = request.form.get("contents")
        api.set(email, contents)

    return redirect(url_for("index"))


"""
API ENDPOINTS
"""


@app.route("/api/user/verify/", methods=["POST"])
@cross_origin()
def api_verify():
    """
    Verify correct token credentials
    for client api calls.
    """
    email = request.form.get("email")
    token = request.form.get("token")

    if not api.verify_token(email, token):
        return make_response("Invalid email or token"), 401

    return make_response("Valid Credentials"), 200


@app.route("/api/user/token/", methods=["POST"])
# @limiter.limit("200 per day, 50 per hour, 10 per minute")
def api_token():
    """
    Verify correct token credentials
    for client api calls.
    """
    email = request.form.get("email")
    password = request.form.get("password")

    if not api.verify_login(email, password):
        return make_response("Invalid email or password"), 401

    return jsonify(api.get_token(email)), 200


@app.route("/api/clipboard/read/", methods=["POST"])
@cross_origin()
def api_read():
    """
    Read from clipboard.
    """
    email = request.form.get("email")
    token = request.form.get("token")

    if not api.verify_token(email, token):
        return make_response("Invalid email or token"), 401

    clipboard = api.read(email)
    return jsonify(clipboard), 200


@app.route("/api/clipboard/set/", methods=["POST"])
@cross_origin()
def api_set():
    """
    Set clipboard.
    """
    email = request.form.get("email")
    token = request.form.get("token")

    if not api.verify_token(email, token):
        return make_response("Invalid email or token"), 401

    contents = request.form.get("contents")

    api.set(email, contents)

    return jsonify("Updated"), 200


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500


@app.errorhandler(429)
def internal_server_error(error):
    retry_after = error.description.split("per")[-1]
    return render_template('429.html', rule=error.description, retry_after=retry_after), 429


@app.route('/_ah/warmup')
def _warmup():
    return "", 200, {}


if __name__ == "__main__":
    app.run(debug=True)
