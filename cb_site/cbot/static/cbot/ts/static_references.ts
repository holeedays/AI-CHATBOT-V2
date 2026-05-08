export class StaticReferences {
    // jquery searching items
    public static readonly JQUERY_USER_INPUT_AREA_ID: string = "#input_area";
    public static readonly JQUERY_CHAT_WINDOW_ID: string = "#chat_window";
    public static readonly JQUERY_SUBMIT_BUTTON_ID: string = "#submit_button";
    public static readonly JQUERY_FONT_SWITCH_BUTTON_ID: string = "#font_switch_button";

    public static readonly JQUERY_QUEUE_TEXT_CONTAINER_ID: string = "#queue"; 
    public static readonly JQUERY_QUEUE_TEXT_MESSAGE_ID: string ="#queue_text_message";
    public static readonly JQUERY_RESPONSE_STREAM_ID: string = "#response_stream";

    public static readonly JQUERY_ID: string = "id";

    // misc

    // for id/class fill ins (not the entire selector tags like "#abc" or ".abc")
    public static readonly QUEUE_CONTAINER_TEXT: string = "queue"; 
    public static readonly QUEUE_TEXT_MESSAGE: string = "queue_text_message";
    public static readonly RESPONSE_STREAM: string = "response_stream";

    public static readonly COMPLETED_RESPONSE: string = "completed_response";
    public static readonly USER_INPUT: string = "user_input";
    public static readonly FONT_SWITCH_ACTIVE_CLASS: string = "is-active";
    public static readonly FONT_SWITCH_PLAIN_CLASS: string = "font-switch-plain";

    public static readonly USER_INPUT_WRAPPER: string = "user_input_wrapper";
    public static readonly AI_RESPONSE_WRAPPER: string = "ai_response_wrapper";

    // template items; allow to be mixed and matched when using jquery selections
    public static readonly USER_HEADER: string = "User:";
    public static readonly AI_HEADER: string = "AIB:";
    public static readonly AI_HEADER_STRONG: string = `<strong>${this.AI_HEADER}</strong>`;

    public static readonly PRE_BLOCK: string = "<pre></pre>";
    public static readonly PARAGRAPH_BLOCK: string = "<p></p>";
    public static readonly DIV_BLOCK: string = "<div></div>";
    public static readonly STRONG_BLOCK: string = "<strong></strong>";
    public static readonly SPAN_BLOCK: string = "<span></span>";

    public static readonly PRE_SELECTOR_TAG: string = "pre";

    public static readonly LOADING_IMAGE_EMBED = '<img class="loading_gif" src="/static/cbot/images/GIFs/loading.gif">';
    public static readonly FONT_SWITCH_LABEL_ON: string = "Plain Font";
    public static readonly FONT_SWITCH_LABEL_OFF: string = "Script Font";

    public static readonly RESPONSE_TEMPLATE: string = `<pre><div id="${this.RESPONSE_STREAM}"></div></pre>`;
    public static readonly QUEUING_TEXT_TEMPLATE: string = `<pre><div id="${this.QUEUE_CONTAINER_TEXT}">${this.AI_HEADER_STRONG}<div class="queue_row">${this.LOADING_IMAGE_EMBED}<span id="${this.QUEUE_TEXT_MESSAGE}"></span></div></div></pre>`;

    // arrays of text
    public static readonly QUEUING_TEXT_PHRASES: [string[], string[], string[], string[], string[]] = [
        ["Parsing request intent...", "Just reading through that now...", "Reviewing your request...", "Understanding your goal..."],
        ["Scanning internal knowledge base...", "Gathering all the relevant facts.", "Gathering the facts.", "Searching for the best info."],
        ["Evaluating multi-step logic...", "Looking for patterns...", "Connecting the ideas.", "Organzing the details."],
        ["Drafting the response...", "Putting it all together.", "Defining your response.", "Creating your answer."],
        ["Finalizing output formatting...", "Almost there... Adding final touches...", "Adding the final touches.", "Checking for accuracy."]
    ];
}
