import { TypingFunctionalities } from "./text_manipulating.js";
class ChatLogic {
    inputArea;
    chatWindow;
    submitButton;
    tt;
    ws;
    constructor() {
        // get all HTML elements
        this.inputArea = $("#input_area");
        this.chatWindow = $("#chat_window");
        this.submitButton = $("#submit_button");
        this.initializeSubmitButton();
        this.initializeEnterKey();
        // establish websocket connection
        // first determine header of connection 
        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        // append that to get our string (the last part should be reflected in our routing.py)
        const socketURL = `${protocol}${window.location.host}/ws/response_stream/`;
        // then initialize it and its functions
        this.ws = new WebSocket(socketURL);
        this.initializeWebsocket();
        // misc
        this.tt = new TypingFunctionalities.TextTyper();
    }
    // connect submit button to a method
    initializeSubmitButton() {
        this.submitButton.on("click", () => this.onSubmit());
    }
    // deal with websocket callbacks
    initializeWebsocket() {
        this.ws.onopen = (ev) => {
            console.log("Websocket has been established");
        };
        this.ws.onclose = (ev) => {
            console.log("Websocket is closing");
        };
        this.ws.onmessage = (ev) => this.onResponse(ev);
        this.ws.onerror = (ev) => { console.error("WebSocket error:", ev); };
    }
    // check for enterkey
    initializeEnterKey() {
        $(document).on("keydown", (event) => {
            if (event.key === "Enter")
                this.onSubmit();
        });
    }
    // our callback when user submits a request
    async onSubmit() {
        // btw, we use .val() instead of .text() for input html elements
        const message = this.inputArea.val();
        if (message === undefined) {
            console.warn("Message is undefined, doing nothing");
            return;
        }
        // add the user to the window chat
        const trimmedMessage = message.trim();
        if (trimmedMessage.length === 0)
            return;
        // create a new object and edit it this way so that the user can't just add raw html
        // to our page
        const userInput = $("<p></p>").addClass("user_input");
        userInput.append($("<strong></strong>").text("User:"));
        userInput.append(document.createTextNode(` ${trimmedMessage}`));
        this.chatWindow.append(userInput);
        this.inputArea.val("");
        // await for a successful reset
        await this.reset();
        const input_JSON = JSON.stringify({
            "message": trimmedMessage
        });
        this.ws.send(input_JSON);
    }
    // reset existing processes (used in onSubmit as a clear all thing)
    async reset() {
        // reset the text typer, removing anything from the queue
        await this.tt.reset();
        // remove the existing response if it exists
        const existing_stream = $("#response_stream");
        if (existing_stream.length != 0) {
            existing_stream.removeAttr("id");
            existing_stream.addClass("completed_response");
        }
    }
    // callback when our websocket gets a response (partial or full)
    onResponse(ev) {
        let responseBody;
        let responseFinished;
        const data = JSON.parse(ev.data);
        // see if these key/value pairs exist
        try {
            responseBody = data["message"];
            responseFinished = data["is_finished"];
        }
        // if not exit out of the method
        catch (error) {
            if (error instanceof (Error))
                console.warn(error.message);
            else
                console.warn("An unidentified error occurred:", error);
            return;
        }
        // find our new response stream
        let newResponse = $("#response_stream");
        // check if it exists, if not, add the element
        if (newResponse.length === 0) {
            this.chatWindow.append(`
                <p id="response_stream">
                    <strong>AIB:</strong>
                </p>
            `);
            newResponse = $("#response_stream");
        }
        // queue the new response to be typed
        const typeSpeedMS = 2;
        this.tt.type(newResponse, responseBody, TypingFunctionalities.TypingStyles.BY_LETTER, typeSpeedMS);
        // also check if response is finished, which we just cue at the end of the response being
        // successfully typed
        if (responseFinished) {
            this.tt.finish();
            newResponse.removeAttr("id");
            newResponse.addClass("completed_response");
        }
    }
}
export default ChatLogic;
//# sourceMappingURL=chat_logic.js.map