const socket = io()

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
 * @param {string} html_string
 * @returns {HTMLElement}
 */
function html_string_to_html_element(html_string) {
    let temp_div = document.createElement("div")
    temp_div.innerHTML = html_string
    return temp_div.firstElementChild
}

function create_message_html_string(message, formatted_date) {
    let message_html_string = message_template
        .replaceAll("[message-body]", message["body"])
        .replaceAll("[date]", formatted_date)
        .replaceAll("[message-origin]", message["origin"])
    
    return message_html_string
}

function create_user_header_html_string(user_info) {
    let user_header_html_string = user_header_template
        .replaceAll("[user-id]", user_info["user_id"])
        .replaceAll("[username]", "@" + user_info["username"])
        .replaceAll("[display-name]", user_info["display_name"])
    
    return user_header_html_string
}

function add_old_message(message) {
    let formatted_date = format_date(message["date_created"])

    let html_string = create_message_html_string(message, formatted_date)

    // hide the date label if the chronologically following message has the same
    // date-sent
    let following_message = message_container.querySelector(".message")
    if (following_message) {
        let following_date = following_message.querySelector(".date-sent").textContent
        if (following_date === formatted_date) {
            html_string = html_string
                .replaceAll(`class="date-sent"`, `class="date-sent hidden"`)
        }
    }

    let element = html_string_to_html_element(html_string)

    message_container.firstElementChild
        .insertAdjacentElement("afterend", element)
}

function add_new_message(message) {
    let formatted_date = format_date(message["date_created"])

    let html_string = create_message_html_string(message, formatted_date)
    let element = html_string_to_html_element(html_string)

    // hide the date label if the previous message has the same date-sent
    let previous_message = Array(...message_container.querySelectorAll(".message")).at(-1)
    if (previous_message) {
        let previous_date_element = previous_message.querySelector(".date-sent")
        let previous_date = previous_date_element.textContent
        if (previous_date === formatted_date) {
            previous_date_element.classList.add("hidden")
        }
    }

    message_container.lastElementChild
        .insertAdjacentElement("afterend", element)
}

function append_nothing_to_load() {
    document.querySelector(".loading-icon").insertAdjacentElement(
        "afterend",
        html_string_to_html_element("<p class='flash-message'>Nothing to show</p>")
    )
}

function add_user_header(user_info) {
    console.log(user_info)

    let html_string = create_user_header_html_string(user_info)
    let element = html_string_to_html_element(html_string)

    document.querySelector(".loading-icon")
        .insertAdjacentElement("beforebegin", element)
}

function request_user_info() {
    let recipient_username = window.location.pathname.split("/").at(-1)
    
    fetch(fetch_user_info_base_url + recipient_username, {method: "GET"})
        .then(resp => {
            let is_json = resp.headers.get('Content-Type') === "application/json"
            return Promise.all([is_json ? resp.json() : resp.text(), resp.ok])
        })
        .then((resp_data) => {
            resp_content = resp_data[0]
            ok = resp_data[1]

            console.log(resp_data)
            if (!ok) {display_error(resp_content)}
            else {add_user_header(resp_content)}
        })
}

function request_messages() {
    let recipient_username = window.location.pathname.split("/").at(-1)
    socket.emit(
        "request_message_history",
        recipient_username = recipient_username,
        cursor = message_cursor_position
    )
}

function register_for_realtime() {
    let recipient_username = window.location.pathname.split("/").at(-1)
    socket.emit(
        "register_for_realtime",
        recipient_username = recipient_username
    )
}

function send_message(message_body) {
    let recipient_username = window.location.pathname.split("/").at(-1)
    socket.emit(
        "send_message",
        recipient_username = recipient_username,
        message_body = message_body
    )
}

function display_error(message) {
    console.log(message)

    let error_str = message
    let error_html_string = `<p class="flash-message">Error - ${error_str}</p>`
    message_form.insertAdjacentHTML("afterend", error_html_string)
}

socket.on("send_message_history", (messages) => {
    console.log(messages)

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
    let last_message = messages.at(-1)
    if (last_message) {
        message_cursor_position = last_message.message_id
    }

    // update load-messages-button visibility
    // theres no more to load or nothing was loaded
    let no_more_to_load = last_message && last_message.message_idx === 1
    if ( no_more_to_load || message_cursor_position === 0 ) {
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
        add_new_message(message)
        message_container.scrollTop = message_container.scrollHeight
    }
})

socket.on("error_response", display_error)