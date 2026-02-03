import Bitter

if __name__ == "__main__":
    # .run does not expect the first argument "app"
    Bitter.run(debug=True)

# general config can be found in Bitter/config.py
# .env should contain the following keys:
#   FLASK_SECRET_KEY : str
#   DB_POOL_SIZE : int
#   DB_HOST : str
#   DB_USER : str
#   DB_PASSWORD : str
#   ADMIN_ACCOUNT_PASSWORD : str

# KOWN ISSUES:
#   @login_required checks if a user_id exists in client-side cookies, which means if said user_id belongs to a deleted
#     user the request passes as logged in. this happens when client-side cookies are outdated after resetting the
#     db. this could be fixed with a db query every time a login_required is used, but that seems excessive for a mostly
#     non-issue
