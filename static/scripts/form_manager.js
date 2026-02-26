
/**
 * @param {SubmitEvent} event 
 */
async function on_form_submit(event) {
    event.preventDefault()
    
    // extract data from the form element
    /** @type {HTMLFormElement} */
    const form = event.target
    const form_data = new FormData(form)

    // add any images
    /** @type {HTMLInputElement[]} */
    const file_inputs = form.querySelectorAll("input[type='file']")
    file_inputs.forEach(file_input => {
        form_data.append(file_input.name, file_input.files[0])
    })

    // add the CSRF token
    if (csrf_token) {
        form_data.append("csrf_token", csrf_token)
    }

    const url = form.getAttribute("action")
    const method = form.getAttribute("method")

    // send the request
    const resp = await fetch(url, {
        method: method,
        body: form_data
    })
    
    // deal with the response
    handle_response(form, resp)
}

/**
 * @param {HTMLFormElement} form
 * @param {Response} resp
 */
async function handle_response(form, resp) {
    // get the response content in json if the Content-Type header says json,
    // otherwise treat it as plain text
    const is_json = resp.headers.get("Content-Type") === "application/json"
    const resp_content = await (is_json ? resp.json() : resp.text())

    // emit an "error" event on error
    if (resp.status >= 400 ) {
        const error_messages = format_error_messages(resp_content)
        error_event = new CustomEvent("response_error", {"detail": error_messages})
        form.dispatchEvent(error_event)
        return
    }

    // emit a "success" event
    success_event = new CustomEvent("response_success", {"detail": resp_content})
    form.dispatchEvent(success_event)
}

function format_error_messages(resp_content) {
    let error_messages = []

    // the error response content is expected to look like:
    // {cause_of_error: ["error1", "error2"]}
    Object.keys(resp_content).forEach(key => {
        error_messages.push(...resp_content[key])
    })

    return error_messages
}