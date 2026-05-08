export class StaticReferences {
    // jquery searching items
    static JQUERY_USER_INPUT_AREA_ID = "#input_area";
    static JQUERY_CHAT_WINDOW_ID = "#chat_window";
    static JQUERY_SUBMIT_BUTTON_ID = "#submit_button";
    static JQUERY_FONT_SWITCH_BUTTON_ID = "#font_switch_button";
    static JQUERY_QUEUE_TEXT_CONTAINER_ID = "#queue";
    static JQUERY_QUEUE_TEXT_MESSAGE_ID = "#queue_text_message";
    static JQUERY_RESPONSE_STREAM_ID = "#response_stream";
    static JQUERY_ID = "id";
    // misc
    // for id/class fill ins (not the entire selector tags like "#abc" or ".abc")
    static QUEUE_CONTAINER_TEXT = "queue";
    static QUEUE_TEXT_MESSAGE = "queue_text_message";
    static RESPONSE_STREAM = "response_stream";
    static COMPLETED_RESPONSE = "completed_response";
    static USER_INPUT = "user_input";
    static FONT_SWITCH_ACTIVE_CLASS = "is-active";
    static FONT_SWITCH_PLAIN_CLASS = "font-switch-plain";
    static USER_INPUT_WRAPPER = "user_input_wrapper";
    static AI_RESPONSE_WRAPPER = "ai_response_wrapper";
    // template items; allow to be mixed and matched when using jquery selections
    static USER_HEADER = "User:";
    static AI_HEADER = "AIB:";
    static AI_HEADER_STRONG = `<strong>${this.AI_HEADER}</strong>`;
    static PRE_BLOCK = "<pre></pre>";
    static PARAGRAPH_BLOCK = "<p></p>";
    static DIV_BLOCK = "<div></div>";
    static STRONG_BLOCK = "<strong></strong>";
    static SPAN_BLOCK = "<span></span>";
    static PRE_SELECTOR_TAG = "pre";
    static LOADING_IMAGE_EMBED = '<img class="loading_gif" src="/static/cbot/images/GIFs/loading.gif">';
    static FONT_SWITCH_LABEL_ON = "Plain Font";
    static FONT_SWITCH_LABEL_OFF = "Script Font";
    static RESPONSE_TEMPLATE = `<pre><div id="${this.RESPONSE_STREAM}"></div></pre>`;
    static QUEUING_TEXT_TEMPLATE = `<pre><div id="${this.QUEUE_CONTAINER_TEXT}">${this.AI_HEADER_STRONG}<div class="queue_row">${this.LOADING_IMAGE_EMBED}<span id="${this.QUEUE_TEXT_MESSAGE}"></span></div></div></pre>`;
    // arrays of text
    static QUEUING_TEXT_PHRASES = [
        ["Parsing request intent...", "Just reading through that now...", "Reviewing your request...", "Understanding your goal..."],
        ["Scanning internal knowledge base...", "Gathering all the relevant facts.", "Gathering the facts.", "Searching for the best info."],
        ["Evaluating multi-step logic...", "Looking for patterns...", "Connecting the ideas.", "Organzing the details."],
        ["Drafting the response...", "Putting it all together.", "Defining your response.", "Creating your answer."],
        ["Finalizing output formatting...", "Almost there... Adding final touches...", "Adding the final touches.", "Checking for accuracy."]
    ];
}
//# sourceMappingURL=static_references.js.map