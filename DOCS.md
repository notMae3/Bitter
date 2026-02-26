<style>
    table td {
        word-break: break-word;
        white-space: normal;

        border: 1px solid #ccc;
        font-size: 11px;
    }

    .response-table td:first-child {border-left: none;}
    .response-table td:last-child {border-right: none;}
    .response-table tr:first-child td {border-top: none;}
    .response-table tr:last-child td {border-bottom: none;}

    .no-wrap {
        word-break: unset;
    }
</style>

# API documentation

> [!NOTE] [content]-idx
Certain application/json responses and socket API events contain an integer called [content]-idx. This index is relative to all items of this content type that are available in the current context.\
For example: If a client fetches replies for a certain post, and the reply-idx of the last reply in the response is 4, then the client knows there are 4 more replies available to load.

## REST API

> [!NOTE] User authentication
All routes with user authentication expects a JWT access token to be present in the cookie-header of the request.\
<code>Admin</code> authentication checks wether the current user is an admin in addition to the check that <code>Logged-in</code> performs.
> <table>
>  <tr>
>    <td><code>Logged-in</code></td>
>    <td>
>      <table class="response-table">
>        <tr> <td>If authentication fails:</td><td>[401] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
>        <tr> <td>If authentication succeeds:</td><td>Whatever the protected path produces</td> </tr>
>      </table>
>    </td>
>  </tr>
>  <tr>
>    <td><code>Admin</code></td>
>    <td>
>      <table class="response-table">
>        <tr> <td>If authentication fails:</td><td>[401] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
>        <tr> <td>If authentication succeeds:</td><td>Whatever the protected path produces</td> </tr>
>      </table>
>    </td>
>  </tr>
> </table>

> [!NOTE] Cross Site Request Forgery (CSRF)
All non-<code>GET</code> API routes expect a csrf_token to be present in the request content.\
This token is automatically generated and included in the forms present in HTML pages produced by non-API routes.
> <table class="response-table">
>   <tr> <td>If csrf_token is missing or malformed:</td><td>[400] [application/json] {"errors": [ <i>"errors": <i>list[str]</i></i> ]}</td> </tr>
>   <tr> <td>If authentication succeeds:</td><td>Whatever the protected path produces</td> </tr>
> </table>

> [!NOTE] Errors
> <table class="response-table">
>   <tr>
>     <td>Database error:</td>
>     <td>[503] [application/json] {"errors": <i>list[str]</i>}</td>
>   </tr>
>   <tr>
>     <td>General HTTP error:</td>
>     <td>[code] [application/json] {"errors": <i>list[str]</i>}</td>
>   </tr>
>   <tr>
>     <td>Critical system error:</td>
>     <td>[500] [application/json] {"errors": <i>list[str]</i>}</td>
>   </tr>
> </table>

<table>
  <tr>
    <th>Method</th>
    <th class="no-wrap">Path</th>
    <th>Minimum user authentication</th>
    <th>Purpose</th>
    <th>Request content</th>
    <th>Response</th>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/uploads/post-images/{post_id}.png</td>
    <td><code>Logged-in</code></td>
    <td>Serves the image correspodning to the inputted post_id</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If the image wasn't found:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the image was found:</td><td>[200] [image/*] <i>Requested image</i> </td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/uploads/user-pfps/{user_id}.png</td>
    <td><code>Logged-in</code></td>
    <td>Serves a profile-picture image corresponding to the inputted user_id</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If the image wasn't found:</td><td>[200] [image/*] <i>Default profile-picture image</i> </td> </tr>
            <tr> <td>If the image was found:</td><td>[200] [image/*] <i>Requested image</i> </td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>POST</code></td>
    <td class="no-wrap">/api/login</td>
    <td></td>
    <td>Login to an account</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {username: str, password: str}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If user doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If password was incorrect:</td><td>[401] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If login was successful:</td><td>[200] [text/plain] <i>Success message and a Set-Cookie header containing the JWT access token</i> </td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>POST</code></td>
    <td class="no-wrap">/api/signup</td>
    <td></td>
    <td>Create a new account</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {display_name: str, username: str, email: str, password}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If username or email was unavailable:</td><td>[409] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If account creation was successful:</td><td>[201] [text/plain] <i>Success message and the values used for account creation, except the password</i> </td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>PUT</code></td>
    <td class="no-wrap">/api/update-profile</td>
    <td><code>Logged-in</code></td>
    <td>Update the currently logged-in user's username and/or profile-picture</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {display-name: str} and/or {pfp: file}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If display-name was passed and was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If profile-picture was passed and the file-content doesn't appear to be an image:</td><td>[415] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If profile-picture was passed and the file-size was too large:</td><td>[400] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If account-update was successful:</td><td>[200] [application/json] {updated_display_name: <i>bool</i>, updated_pfp: <i>bool</i>, new_display_name: <i>str</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>POST</code></td>
    <td class="no-wrap">/api/create-post</td>
    <td><code>Logged-in</code></td>
    <td>Create a new post as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {post-body: str, image: file}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If image was passed and the file-content doesn't appear to be an image:</td><td>[415] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If image was passed and the file-size was too large:</td><td>[400] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If post creation was successful:</td><td>[201] [application/json] {post_id: <i>int</i>, author_id: <i>int</i>, date_created: <i>int</i>, body: <i>str</i>, contains_image: <i>int</i>, view_count: <i>int</i>, like_count: <i>int</i>, reply_count: <i>int</i>, author_username: <i>str</i>, author_display_name: <i>str</i>, user_liked: <i>int</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>POST</code></td>
    <td class="no-wrap">/api/create-reply</td>
    <td><code>Logged-in</code></td>
    <td>Create a new reply as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {reply-body: str, parent-post-id: int}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If reply creation was successful:</td><td>[201] [application/json] {reply_id: <i>int</i>, parent_post_id: <i>int</i>, author_id: <i>int</i>, date_created: <i>int</i>, body: <i>str</i>, author_username: <i>str</i>, author_display_name: <i>str</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>POST</code></td>
    <td class="no-wrap">/api/create-conversation</td>
    <td><code>Logged-in</code></td>
    <td>Create a new conversation as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {username: str}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If a user with the inputted username doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If a conversation between the inputted username and the current user already exists:</td><td>[409] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the inputted username belongs to the current user:</td><td>[400] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If conversation creation was successful:</td><td>[201] [application/json] {conversation_id: <i>int</i>, date_created: <i>int</i>, contains_unseen_messages: <i>int</i>, recipient_user_id: <i>int</i>, recipient_display_name: <i>str</i>, recipient_username: <i>str</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/fetch-posts?cursor={int}</td>
    <td><code>Logged-in</code></td>
    <td>Fetch posts</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If the post-fetching was successful:</td><td>[200] [application/json] [ {post_id: <i>int</i>, author_id: <i>int</i>, date_created: <i>int</i>, body: <i>str</i>, contains_image: <i>int</i>, view_count: <i>int</i>, like_count: <i>int</i>, reply_count: <i>int</i>, author_username: <i>str</i>, author_display_name: <i>str</i>, user_liked: <i>int</i>}, ]</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/fetch-post?post_id={int}</td>
    <td><code>Logged-in</code></td>
    <td>Fetch a singular post</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If the post-fetching was successful:</td><td>[200] [application/json] {post_id: <i>int</i>, author_id: <i>int</i>, date_created: <i>int</i>, body: <i>str</i>, contains_image: <i>int</i>, view_count: <i>int</i>, like_count: <i>int</i>, reply_count: <i>int</i>, author_username: <i>str</i>, author_display_name: <i>str</i>, user_liked: <i>int</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/fetch-replies?post_id={int}&cursor={int}</td>
    <td><code>Logged-in</code></td>
    <td>Fetch replies</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If the reply-fetching was successful:</td><td>[200] [application/json] [ {reply_id: <i>int</i>, parent_post_id: <i>int</i>, author_id: <i>int</i>, date_created: <i>int</i>, body: <i>str</i>, author_username: <i>str</i>, author_display_name: <i>str</i>, reply_idx: <i>int</i>}, ]</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/fetch-conversations?cursor={int}</td>
    <td><code>Logged-in</code></td>
    <td>Fetch conversations</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If the reply-fetching was successful:</td><td>[200] [application/json] [ {conversation_id: <i>int</i>, date_created: <i>int</i>, contains_unseen_messages: <i>int</i>, recipient_user_id: <i>int</i>, recipient_display_name: <i>str</i>, recipient_username: <i>str</i>, conversation_idx: <i>int</i>}, ]</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/fetch-own-profile</td>
    <td><code>Logged-in</code></td>
    <td>Fetch information about the currently logged-in user</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If the currently logged-in user somehow doesn't exist :</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the user-information fetch was successful:</td><td>[200] [application/json] {display_name: <i>str</i>, username: <i>str</i>, user_id: <i>int</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>GET</code></td>
    <td class="no-wrap">/api/fetch-profile-from-username?username={str}</td>
    <td><code>Logged-in</code></td>
    <td>Fetch information about the user with the inputted username</td>
    <td></td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If a user with the inputted username doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the user-information fetch was successful:</td><td>[200] [application/json] {user_id: <i>int</i>, display_name: <i>str</i>, username: <i>str</i>}</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>PUT</code></td>
    <td class="no-wrap">/api/like-post</td>
    <td><code>Logged-in</code></td>
    <td>Like a post as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {post_id: int}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If a post with the inputted post_id doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the current user has already liked the post with the inputted post_id:</td><td>[409] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the like-operation was successful:</td><td>[200] [text/plain] <i>Success message</i></td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>PUT</code></td>
    <td class="no-wrap">/api/unlike-post</td>
    <td><code>Logged-in</code></td>
    <td>Unlike a post as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {post_id: int}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If a post with the inputted post_id doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the current user hasn't liked the post with the inputted post_id:</td><td>[409] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the unlike-operation was successful:</td><td>[200] [text/plain] <i>Success message</i></td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>DELETE</code></td>
    <td class="no-wrap">/api/delete-post</td>
    <td><code>Admin</code></td>
    <td>Delete a post as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {post_id: int}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If a post with the inputted post_id doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the reply-deletion was successful:</td><td>[204]</td> </tr>
        </table>
    </td>
  </tr>
  <tr>
    <td><code>DELETE</code></td>
    <td class="no-wrap">/api/delete-reply</td>
    <td><code>Admin</code></td>
    <td>Delete a reply as the currently logged-in user</td>
    <td>
        [multipart/form-data; boundary= <i>boundary</i> ]<br>
        {reply_id: int}
    </td>
    <td>
        <table class="response-table">
            <tr> <td>If an input value was malformed:</td><td>[400] [application/json] { <i>Malformed value key</i> : <i>list[str]</i>, }</td> </tr>
            <tr> <td>If a reply with the inputted reply_id doesn't exist:</td><td>[404] [application/json] {"errors": <i>list[str]</i>}</td> </tr>
            <tr> <td>If the post-deletion was successful:</td><td>[204]</td> </tr>
        </table>
    </td>
  </tr>
</table>

## Socket API

> [!NOTE] User authentication
> All events with user authentication expects a JWT access token to be present in the cookie-header of the request.\
> <code>Admin</code> authentication checks wether the current user is an admin in addition to the check that <code>Logged-in</code> performs.
> <table>
>  <tr>
>    <td><code>Logged-in</code></td>
>    <td>
>      <table class="response-table">
>        <tr> <td>If authentication fails:</td><td><i>Emits "error_response"</i></td> </tr>
>        <tr> <td>If authentication succeeds:</td><td>Whatever the protected event produces</td> </tr>
>      </table>
>    </td>
>  </tr>
>  <tr>
>    <td><code>Admin</code></td>
>    <td>
>      <table class="response-table">
>        <tr> <td>If authentication fails:</td><td><i>Emits "error_response"</i></td> </tr>
>        <tr> <td>If authentication succeeds:</td><td>Whatever the protected event produces</td> </tr>
>      </table>
>    </td>
>  </tr>
> </table>

> [!NOTE] Errors
> <table class="response-table">
>   <tr>
>     <td>Database error:</td>
>     <td><i>Emits "error_response"</i></td>
>   </tr>
>   <tr>
>     <td>Critical system error:</td>
>     <td><i>Emits "error_response"</i></td>
>   </tr>
> </table>

<table>
  <tr>
    <th class="no-wrap">Event name</th>
    <th>Emitted from</th>
    <th>Minimum user authentication</th>
    <th>Purpose</th>
    <th>Expected event content</th>
  <tr>
  <tr>
    <td class="no-wrap">"connect"</td>
    <td>Server & Client</td>
    <td></td>
    <td>Tells the server & client when a client has connected</td>
    <td></td>
  </tr>
  <tr>
    <td class="no-wrap">"disconnect"</td>
    <td>Server & Client</td>
    <td></td>
    <td>Tells the server & client when a client has disconnected</td>
    <td></td>
  </tr>
  <tr>
    <td class="no-wrap">"register_for_realtime"</td>
    <td>Client</td>
    <td><code>Logged-in</code></td>
    <td>Register a client to a server-side socket-room, which enables real-time messaging with other room members</td>
    <td>{recipient_username: <i>str</i>}</td>
  </tr>
  <tr>
    <td class="no-wrap">"request_message_history"</td>
    <td>Client</td>
    <td><code>Logged-in</code></td>
    <td>Fetch the message history of a conversation</td>
    <td>{recipient_username: <i>str</i>, cursor: <i>str | int</i>}</td>
  </tr>
  <tr>
    <td class="no-wrap">"send_message"</td>
    <td>Client</td>
    <td><code>Logged-in</code></td>
    <td>Send a new message in a conversation</td>
    <td>{recipient_username: <i>str</i>, message_body: <i>str</i>}</td>
  </tr>
  <tr>
    <td class="no-wrap">"send_message_history"</td>
    <td>Server</td>
    <td></td>
    <td>Sends the message history of a conversation to the user that requested it</td>
    <td>{messages: [ {message_id: <i>int</i>, author_id: <i>int</i>, body: <i>str</i>, date_created: <i>int</i>, conversation_id: <i>int</i>, seen: <i>int</i>, message_idx: <i>int</i>, origin: <i>str</i>}, ]}</td>
  </tr>
  <tr>
    <td class="no-wrap">"new_message_created"</td>
    <td>Server</td>
    <td></td>
    <td>Send a newly created message to each member of a socket-room</td>
    <td>{message: {message_id: <i>int</i>, author_id: <i>int</i>, body: <i>str</i>, date_created: <i>int</i>, conversation_id: <i>int</i>, seen: <i>int</i>, message_idx: <i>int</i>, origin: <i>str</i>}}</td>
  </tr>
  <tr>
    <td class="no-wrap">"error_response"</td>
    <td>Server</td>
    <td></td>
    <td>Send an error to the client that requested something</td>
    <td>{message: <i>str</i>}</td>
  </tr>
</table>
