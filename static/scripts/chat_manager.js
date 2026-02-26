const socket = io()

function format_date(seconds) {
    const date = new Date(seconds*1000)
    return "" + date.getFullYear() + "-"
              + (date.getMonth()+1).toString().padStart(2, "0") + "-"
              + date.getDate().toString().padStart(2, "0") + " "
              + date.getHours().toString().padStart(2, "0") + ":"
              + date.getMinutes().toString().padStart(2, "0") + " UTC+"
              + (-date.getTimezoneOffset()/60)
}

/**
 * @param {string} html_string
 * @returns {HTMLElement}
 */
function html_string_to_html_element(html_string) {
    const temp_div = document.createElement("div")
    temp_div.innerHTML = html_string
    return temp_div.firstElementChild
}

function create_message_html_string(message, formatted_date) {
    const message_html_string = message_template
        .replaceAll("[message-body]", message["body"])
        .replaceAll("[date]", formatted_date)
        .replaceAll("[message-origin]", message["origin"])
    
    return message_html_string
}

function create_user_header_html_string(user_info) {
    const user_header_html_string = user_header_template
        .replaceAll("[user-id]", user_info["user_id"])
        .replaceAll("[username]", "@" + user_info["username"])
        .replaceAll("[display-name]", user_info["display_name"])
    
    return user_header_html_string
}

function add_old_message(message) {
    const formatted_date = format_date(message["date_created"])

    let html_string = create_message_html_string(message, formatted_date)

    // hide the date label if the chronologically following message has the same
    // date-sent
    const following_message = message_container.querySelector(".message")
    if (following_message) {
        const following_date = following_message.querySelector(".date-sent").textContent
        if (following_date === formatted_date) {
            html_string = html_string
                .replaceAll(`class="date-sent"`, `class="date-sent hidden"`)
        }
    }

    const element = html_string_to_html_element(html_string)

    message_container.firstElementChild
        .insertAdjacentElement("afterend", element)
}

function add_new_message(message) {
    const formatted_date = format_date(message["date_created"])

    const html_string = create_message_html_string(message, formatted_date)
    const element = html_string_to_html_element(html_string)

    // hide the date label if the previous message has the same date-sent
    const previous_message = Array(...message_collection).at(-1)
    if (previous_message) {
        const previous_date_element = previous_message.querySelector(".date-sent")
        const previous_date = previous_date_element.textContent
        if (previous_date === formatted_date) {
            previous_date_element.classList.add("hidden")
        }
    }

    message_container.lastElementChild
        .insertAdjacentElement("afterend", element)
}

function add_user_header(user_info) {
    const html_string = create_user_header_html_string(user_info)
    const element = html_string_to_html_element(html_string)

    document.querySelector(".loading-icon")
        .insertAdjacentElement("beforebegin", element)
}

async function request_user_info() {
    const recipient_username = window.location.pathname.split("/").at(-1)

    const resp = await fetch(fetch_user_info_base_url + recipient_username, {method: "GET"})

    const is_json = resp.headers.get('Content-Type') === "application/json"
    const resp_content = await (is_json ? resp.json() : resp.text)
    
    if (!resp.ok) {display_error(resp_content)}
    else          {add_user_header(resp_content)}
}

function request_messages() {
    const recipient_username = window.location.pathname.split("/").at(-1)
    socket.emit(
        "request_message_history",
        recipient_username,
        message_cursor_position
    )
}

function register_for_realtime() {
    const recipient_username = window.location.pathname.split("/").at(-1)
    socket.emit(
        "register_for_realtime",
        recipient_username
    )
}

function send_message(message_body) {
    const recipient_username = window.location.pathname.split("/").at(-1)
    socket.emit(
        "send_message",
        recipient_username,
        message_body
    )
}

function display_error(message) {
    // remove any previous error message
    clear_global_flash_messages()

    const error_html_string = `<p class="flash-message">Error - ${message}</p>`
    message_form.insertAdjacentHTML("afterend", error_html_string)
}

socket.on("connect", () => {
    Array(...message_collection)
        .forEach(element => element.remove())

    message_cursor_position = 0

    request_messages()
    register_for_realtime()
})

socket.on("send_message_history", (messages) => {
    console.log(messages)
    clear_global_flash_messages()

    // if the socket reply doesnt contain the expected messages
    if (!messages || !Object.keys(messages).length || "error" in messages) {
        load_messages_button.classList.add("hidden")
    } else {
        messages.forEach(add_old_message)
    }

    // scroll to the bottom of the message container if its the first message
    // fetch
    if (message_cursor_position === 0) {
        message_container.scrollTop = 10e10
    }

    // update cursor position
    const last_message = messages.at(-1)
    if (last_message) {
        message_cursor_position = last_message.message_id
    }

    // update load-messages-button visibility
    // theres no more to load or nothing was loaded
    const no_more_to_load = last_message && last_message.message_idx === 1
    const nothing_was_loaded = !message_cursor_position

    // tell the user that loading finished and yielded nothing
    if (nothing_was_loaded) {
        loading_icon.insertAdjacentHTML(
            "afterend",
            "<p class='flash-message'>Nothing to show here</p>"
        )
    }

    if ( no_more_to_load || nothing_was_loaded ) {
        load_messages_button.classList.add("hidden")
    }
    // theres more to load
    else {
        load_messages_button.classList.remove("hidden")
    }

    loading_icon.classList.add("hidden")
})

socket.on("new_message_created", (message) => {
    console.log(message)

    // if the socket reply doesnt contain the expected messages
    if (!message || "error" in message) {
        load_messages_button.classList.add("hidden")
    } else {
        // remove old messages
        clear_global_flash_messages()

        add_new_message(message)
        message_container.scrollTop = message_container.scrollHeight
    }
})

socket.on("error_response", (message) => {
    console.log(message)
    display_error(message)
})