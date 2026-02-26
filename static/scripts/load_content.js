function _format_date(seconds) {
    const date = new Date(seconds*1000)
    return "" + date.getFullYear() + "-"
              + (date.getMonth()+1).toString().padStart(2, "0") + "-"
              + date.getDate().toString().padStart(2, "0") + " "
              + date.getHours().toString().padStart(2, "0") + ":"
              + date.getMinutes().toString().padStart(2, "0") + " UTC+"
              + (-date.getTimezoneOffset()/60)
}


/**
 * @param {object} reply
 * @param {string} reply_template
 * @returns {string}
 */
function _generate_reply_html_string(reply, reply_template) {
    const html_string = reply_template
        .replaceAll("[reply-element-id]", "reply-" + reply.reply_id)
        .replaceAll("[body]", reply.body)
        .replaceAll("[user-id]", reply.author_id)
        .replaceAll("[display-name]", reply.author_display_name)
        .replaceAll("[username]", "@" + reply.author_username)
        .replaceAll("[date]", _format_date(reply.date_created))
    
    return html_string
}

/**
 * @param {object} post
 * @param {string} post_template
 * @returns {string}
 */
function _generate_post_html_string(post, post_template) {
    // use reply html string since posts and replies are very similar data wise
    let html_string = _generate_reply_html_string(post, post_template)
        .replaceAll("[post-element-id]", "post-" + post.post_id)
        .replaceAll("[post-id]", post.post_id)
        .replaceAll("[reply-count]", post.reply_count)
        .replaceAll("[like-count]", post.like_count)
        .replaceAll("[view-count]", post.view_count)

    if (post.user_liked) {
        html_string = html_string.replace(
            `class="like-parent"`,
            `class="like-parent active"`
        )
    }

    if (!post.contains_image) {
        html_string = html_string.replace(
            RegExp(`(<div class="img-container">.+?<\/div>)`),
            ""
        )
    }
    
    return html_string
}

/**
 * @param {object} conversation
 * @param {string} conversation_template
 * @returns {string}
 */
function _generate_conversation_html_string(conversation, conversation_template) {
    let html_string = conversation_template
        .replaceAll("[conversation-id]", "conversation-" + conversation.conversation_id)
        .replaceAll("[user-id]", conversation.recipient_user_id)
        .replaceAll("[display-name]", conversation.recipient_display_name)
        .replaceAll("[username]", "@" + conversation.recipient_username)
        .replaceAll("[date]", _format_date(conversation.date_created))
    
    if (!conversation.contains_unseen_messages) {
        html_string = html_string.replaceAll(
            `class="unseen-icon"`, `class="unseen-icon hidden"`)
    }

    return html_string
}

/**
 * @param {string} html_string
 * @returns {HTMLElement}
 */
function _html_string_to_html_element(html_string) {
    const temp_div = document.createElement("div")
    temp_div.innerHTML = html_string
    return temp_div.firstElementChild
}

/**
 * @param {object} post
 * @param {HTMLElement} post_element
 */
function _apply_post_event_listeners(post, post_element) {
    if (is_timeline) {
        post_element.addEventListener("click", () => {open_post(post.post_id)})
    }

    // make clicking on the like button inform the server about it
    post_element.querySelector(".like-parent") // like button
        .addEventListener("click", (event) => {
            like_post(post.post_id)
            event.stopPropagation()
        }
    )

    const delete_button = post_element.querySelector(".delete-button")
    if (delete_button) {
        delete_button.addEventListener("click", async (event) => {
            event.stopPropagation()

            const form_data = new FormData()
            form_data.append("post_id", post["post_id"])
            
            if (csrf_token) {
                form_data.append("csrf_token", csrf_token)
            }

            const resp = await fetch(delete_post_url, {
                method: "DELETE",
                body: form_data
            })
            if (resp.ok) {
                if (is_timeline) {post_element.remove()}
                else {window.location = timeline_url}
            }
        })
    }

    // make clicking on the post image pull up the image inspector
    if (post.contains_image) {
        post_element.querySelector(".img-container")
            .addEventListener("click", (event) => {
                event.stopPropagation()

                const img_inspector = document.getElementById("image-inspector")
                img_inspector.querySelector("img").src = base_post_img_url + `/${post["post_id"]}.png`
                img_inspector.classList.toggle("hidden")
            }
        )
    }
}

/**
 * @param {object} reply
 * @param {HTMLElement} reply_element
 */
function _apply_reply_event_listeners(reply, reply_element) {
    const delete_button = reply_element.querySelector(".delete-button")
    if (!delete_button) {
        return
    }

    delete_button.addEventListener("click", async (event) => {
        event.stopPropagation()

        const form_data = new FormData()
        form_data.append("reply_id", reply["reply_id"])
        if (csrf_token) {
            form_data.append("csrf_token", csrf_token)
        }

        const resp = await fetch(delete_reply_url, {
            method: "DELETE",
            body: form_data
        })

        if (resp.ok) {reply_element.remove()}
    })
}

/**
 * @param {object} conversation
 * @param {HTMLElement} conversation_element
 */
function _apply_conversation_event_listeners(conversation, conversation_element) {
    conversation_element.addEventListener("click", () => {
        open_conversation(conversation.recipient_username)}
    )
}

function append_reply(reply, reply_parent, reply_template, insert_first = false) {
    if (!reply) return

    const html_string = _generate_reply_html_string(reply, reply_template)
    const reply_element = _html_string_to_html_element(html_string)
    _apply_reply_event_listeners(reply, reply_element)
    
    // insert the new element at the top of post parent
    if (insert_first) {insert_as_first_child(reply_parent, reply_element)}
    else {reply_parent.appendChild(reply_element)}
}

function append_post(post, post_parent, post_template, insert_first = false) {
    if (!post) return

    const html_string = _generate_post_html_string(post, post_template)
    const post_element = _html_string_to_html_element(html_string)
    _apply_post_event_listeners(post, post_element)
    
    // insert the new element at the top of post parent
    if (insert_first) {insert_as_first_child(post_parent, post_element)}
    else {post_parent.appendChild(post_element)}
}

function append_conversation(conversation, conversation_parent, conversation_template, insert_first = false) {
    if (!conversation) return

    const html_string = _generate_conversation_html_string(conversation, conversation_template)
    const conversation_element = _html_string_to_html_element(html_string)
    _apply_conversation_event_listeners(conversation, conversation_element)
    
    // insert the new element at the top of post parent
    if (insert_first) {insert_as_first_child(conversation_parent, conversation_element)}
    else {conversation_parent.appendChild(conversation_element)}
}

/**
 * @param {HTMLElement} loading_icon
 */
function append_nothing_to_load(loading_icon) {
    loading_icon.insertAdjacentHTML(
        "afterend",
        "<p class='flash-message'>Nothing to show here</p>"
    )
}

/**
 * Insert a new html element as the first child of the parent element
 * @param {HTMLElement} parent_element
 * @param {HTMLElement} new_element
 */
function insert_as_first_child(parent_element, new_element) {
    if (parent_element.childElementCount) {
        parent_element.firstElementChild.insertAdjacentElement("beforebegin", new_element)
    } else {
        parent_element.appendChild(new_element)
    }
}

/**
 * Attempt to fetch content from the given url. If not Ok add an error message to the given parent_element
 * @param {string} url
 * @param {HTMLElement} parent_element
 * @returns {null | []} null if the fetch response isn't Ok. Otherwise return the response contents in json. 
 */
async function attempt_to_fetch_content(url, parent_element) {
    const resp = await fetch(url, {method: "GET"})

    const is_json = resp.headers.get('Content-Type') === "application/json"
    const resp_content = await (is_json ? resp.json() : resp.text)

    if (!resp.ok) {
        // remove old messages
        parent_element.querySelectorAll(".flash-message")
            .forEach(element => element.remove())
        parent_element.innerHTML += "<p class='flash-message'>Error when loading content</p"
        return null
    }

    // resp_content is expected to be in json since the response status was Ok
    return resp_content
}
