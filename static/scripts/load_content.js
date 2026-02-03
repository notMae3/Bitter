
function format_date(seconds) {
    let date = new Date(seconds*1000)
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
function generate_reply_html_string(reply, reply_template) {
    let html_string = reply_template
        .replaceAll("[reply-element-id]", "reply-" + reply.reply_id)
        .replaceAll("[body]", reply.body)
        .replaceAll("[user-id]", reply.author_id)
        .replaceAll("[display-name]", reply.author_display_name)
        .replaceAll("[username]", "@" + reply.author_username)
        .replaceAll("[date]", format_date(reply.date_created))
    
    return html_string
}

/**
 * @param {object} post
 * @param {string} post_template
 * @returns {string}
 */
function generate_post_html_string(post, post_template) {
    // use reply html string since posts and replies are very similar data wise
    let html_string = generate_reply_html_string(post, post_template)
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
function generate_conversation_html_string(conversation, conversation_template) {
    let html_string = conversation_template
        .replaceAll("[conversation-id]", "conversation-" + conversation.conversation_id)
        .replaceAll("[user-id]", conversation.recipient_user_id)
        .replaceAll("[display-name]", conversation.recipient_display_name)
        .replaceAll("[username]", "@" + conversation.recipient_username)
        .replaceAll("[date]", format_date(conversation.date_created))
    
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
function html_string_to_html_element(html_string) {
    let temp_div = document.createElement("div")
    temp_div.innerHTML = html_string
    return temp_div.firstElementChild
}

/**
 * @param {object} post
 * @param {HTMLElement} post_element
 */
function apply_post_event_listeners(post, post_element) {
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

    let delete_button = post_element.querySelector(".delete-button")
    if (delete_button) {
        delete_button.addEventListener("click", (event) => {
            event.stopPropagation()

            console.log(`del post ${post["post_id"]}`)
            fetch(delete_post_url + post["post_id"], {method: "DELETE"})
                .then(resp =>  {
                    if (resp.ok) {
                        if (is_timeline) {post_element.remove()}
                        else {window.location = timeline_url}
                    }}
                )
        })
    }

    // make clicking on the post image pull up the image inspector
    if (post.contains_image) {
        post_element.querySelector(".img-container")
            .addEventListener("click", (event) => {
                event.stopPropagation()

                let img_inspector = document.getElementById("image-inspector")
                img_inspector.querySelector("img").setAttribute(
                    "src",
                    base_post_img_url + `/${post["post_id"]}.png`
                )

                img_inspector.classList.toggle("hidden")
            }
        )
    }
}

/**
 * @param {object} reply
 * @param {HTMLElement} reply_element
 */
function apply_reply_event_listeners(reply, reply_element) {
    let delete_button = reply_element.querySelector(".delete-button")
    if (!delete_button) {
        return
    }

    delete_button.addEventListener("click", (event) => {
        event.stopPropagation()

        console.log(`del reply ${reply["reply_id"]}`)
        fetch(delete_reply_url + reply["reply_id"], {method: "DELETE"})
            .then(resp =>  {
                if (resp.ok) {reply_element.remove()}
            }
        )
    })
}

/**
 * @param {object} conversation
 * @param {HTMLElement} conversation_element
 */
function apply_conversation_event_listeners(conversation, conversation_element) {
    conversation_element.addEventListener("click", () => {
        open_conversation(conversation.recipient_username)}
    )
}

function append_reply(reply, reply_parent, reply_template) {
    if (!reply) return

    let html_string = generate_reply_html_string(reply, reply_template)
    let reply_element = html_string_to_html_element(html_string)
    apply_reply_event_listeners(reply, reply_element)
    reply_parent.appendChild(reply_element)
}

function append_post(post, post_parent, post_template) {
    if (!post) return

    let html_string = generate_post_html_string(post, post_template)
    let post_element = html_string_to_html_element(html_string)
    apply_post_event_listeners(post, post_element)
    post_parent.appendChild(post_element)
}

function append_conversation(conversation, conversation_parent, conversation_template) {
    if (!conversation) return

    let html_string = generate_conversation_html_string(conversation, conversation_template)
    let conversation_element = html_string_to_html_element(html_string)
    apply_conversation_event_listeners(conversation, conversation_element)
    conversation_parent.appendChild(conversation_element)
}

function append_nothing_to_load() {
    document.querySelector(".loading-icon").insertAdjacentElement(
        "afterend",
        html_string_to_html_element("<p class='flash-message'>Nothing to show</p>")
    )
}

/**
 * @param {string} fetch_url
 * @param {string} content_type
 * @param {HTMLElement} element_parent
 */
async function load(fetch_url, content_type, element_parent, template) {
    let resp = await fetch(fetch_url, {method: "GET"})
    if (!resp.ok) {
        element_parent.innerHTML += "<p class='flash-message'>Error when loading content</p"

        let is_json = resp.headers.get('Content-Type') === "application/json"
        Promise.all([is_json ? resp.json() : resp.text(), resp.ok])
            .then(resp_data => console.log(resp_data))
        
        return
    }

    let json = await resp.json()

    console.log(json)

    let append_function
    switch (content_type) {
        case "post":
            append_function = append_post
            break
        case "reply":
            append_function = append_reply
            break
        case "conversation":
            append_function = append_conversation
            break
    }

    json.forEach(data_obj => {
        append_function(data_obj, element_parent, template)
    })

    return json.at(-1)
}
