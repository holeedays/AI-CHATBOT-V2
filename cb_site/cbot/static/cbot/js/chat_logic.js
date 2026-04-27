import TextManipulator from "./visuals.js";
class ChatLogic {
    ws;
    inputArea;
    chatWindow;
    submitButton;
    tm;
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
        this.tm = new TextManipulator();
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
    }
    // check for enterkey
    initializeEnterKey() {
        $(document).on("keydown", (event) => {
            if (event.key === "Enter")
                this.onSubmit();
        });
    }
    // our callback when user submits a request
    onSubmit() {
        // btw, we use .val() instead of .text() for input html elements
        const message = this.inputArea.val();
        if (this.ws.readyState === WebSocket.CLOSED || message === undefined) {
            console.warn("Either the current websocket connection is closed or message is undefined");
            return;
        }
        this.chatWindow.append(`
            <p id="user_input">
                <strong>User:</strong> ${message}
            </p>
        `);
        const input_JSON = JSON.stringify({
            "message": message
        });
        this.inputArea.val("");
        this.ws.send(input_JSON);
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
        this.tm.type(newResponse, responseBody, 300);
        // also check if response is finished, which we just cue at the end of the response being
        // successfully typed
        if (responseFinished) {
            this.tm.addToQueue(() => new Promise((resolve) => {
                newResponse.attr("id", "completed_response");
            }));
        }
    }
}
export default ChatLogic;
//# sourceMappingURL=chat_logic.js.map