# Bitter
A fully functional and slightly watered-down twitter-like website made for a school assignment. Features most of the functionality you'd expect to see on twitter— that is: posting, liking, replying and real-time chatting. Made using Flask, Jinja, MySQL, MariaDB and SocketIO.

## Stay-logged-in philosophy
Once a user logs in they receive an access token which allows them to make requests to protected routes. This access token is automatically renewed every time the user visits one of the main pages. The access token expires some time after the last time the user visited the website, meaning if you're a frequent visitor you don't have to log back in.

## Useful files
* All API documentation can be found in ```./DOCS.md```
* General config can be found in ```./Bitter/config.py```
* Some pre-made demo data can be found in ```./Bitter-demo.sql```. The "admin" account uses password "pass123" and "bobo" uses password "BobsSuperSecretPassword".

## Dependencies
* MariaDB: 10.4.32
* See ```./requirements.txt```

## ```./.env``` structure
<table>
  <tr>
    <th>Value key</th>
    <th>Value type</th>
    <th>Default value</th>
  </tr>
  <tr>
    <td>FLASK_SECRET_KEY</td>
    <td>str</td>
    <td>"SuperSecretAndCoolFlaskSecretKey"</td>
  </tr>
  <tr>
    <td>DB_POOL_SIZE</td>
    <td>int</td>
    <td>5</td>
  </tr>
  <tr>
    <td>DB_HOST</td>
    <td>str</td>
    <td>"localhost"</td>
  </tr>
  <tr>
    <td>DB_USER</td>
    <td>str</td>
    <td>"root"</td>
  </tr>
  <tr>
    <td>DB_PASSWORD</td>
    <td>str</td>
    <td>""</td>
  </tr>
  <tr>
    <td>ADMIN_ACCOUNT_PASSWORD</td>
    <td>str</td>
    <td>"pass123"</td>
  </tr>
</table>

##

> [!WARNING] Known issues
> 1. ```@login_required``` checks if a user_id exists in client-side cookies, which means if said user_id belongs to a deleted 
user the request passes as logged in. This happens when client-side cookies are outdated after resetting the 
db. This could be fixed with a db query every time a login_required is used, but that seems excessive for a mostly 
non-issue.

> [!NOTE] Cookies
This project doesn't have a cookie-disclaimer banner, which likely isn't compliant with cookie consent laws. That said, the only cookies used by this project are for storing login information.


> [!NOTE] Further improvements
Naturally there's more performance optimizations to be made, however most of these would only matter for a large scale platform. If this project ever became a large scale platform I imagine there would be greater concerns than something like packaging and serializing data, as opposed to sending JSON, when fetching posts.
