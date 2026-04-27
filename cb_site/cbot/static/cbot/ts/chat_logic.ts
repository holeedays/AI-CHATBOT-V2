import TextManipulator from "./visuals.ts";

class ChatLogic {
    private ws: WebSocket;

    private inputArea: JQuery<HTMLInputElement>;
    private chatWindow: JQuery<HTMLDivElement>;
    private submitButton: JQuery<HTMLButtonElement>;

    private tm: TextManipulator;
    
    constructor() {
        // get all HTML elements
        this.inputArea = $("#input_area") as JQuery<HTMLInputElement>;
        this.chatWindow = $("#chat_window") as JQuery<HTMLDivElement>;

        this.submitButton = $("#submit_button") as JQuery<HTMLButtonElement>;
        this.initializeSubmitButton();

        this.initializeEnterKey();

        // establish websocket connection

        // first determine header of connection 
        const protocol: string = window.location.protocol === "https:" ? "wss://" : "ws://"
        // append that to get our string (the last part should be reflected in our routing.py)
        const socketURL: string = `${protocol}${window.location.host}/ws/response_stream/`

        // then initialize it and its functions
        this.ws = new WebSocket(socketURL);
        this.initializeWebsocket();

        // misc
        this.tm = new TextManipulator();
    }

    // connect submit button to a method
    private initializeSubmitButton(): void {
        this.submitButton.on("click", () => this.onSubmit());
    }

    // deal with websocket callbacks
    private initializeWebsocket(): void {
        this.ws.onopen = (ev: Event) => {
            console.log("Websocket has been established");
        }

        this.ws.onclose = (ev: CloseEvent) => {
            console.log("Websocket is closing");
        }

        this.ws.onmessage = (ev: MessageEvent) => this.onResponse(ev);
    }

    // check for enterkey
    private initializeEnterKey(): void {
        $(document).on("keydown", (event: JQuery.KeyDownEvent) => {
            if (event.key === "Enter")
                this.onSubmit();
        });        
    }

    // our callback when user submits a request
    private onSubmit(): void {
        // btw, we use .val() instead of .text() for input html elements
        const message: string | undefined = this.inputArea.val();

        if (this.ws.readyState === WebSocket.CLOSED || message === undefined) {
            console.warn("Either the current websocket connection is closed or message is undefined");
            return;
        }

        this.chatWindow.append(`
            <p id="user_input">
                <strong>User:</strong> ${message}
            </p>
        `);

        const input_JSON: string = JSON.stringify({
            "message": message
        });
        this.inputArea.val("");
        
        this.ws.send(input_JSON);
    }

    // callback when our websocket gets a response (partial or full)
    private onResponse(ev: MessageEvent): void {
        let responseBody: string;
        let responseFinished: boolean;
        const data = JSON.parse(ev.data);

        // see if these key/value pairs exist
        try {
            responseBody = data["message"];
            responseFinished = data["is_finished"];
        }
        // if not exit out of the method
        catch (error) {
            if (error instanceof(Error))
                console.warn(error.message);
            else
                console.warn("An unidentified error occurred:", error);

            return;
        }

        // find our new response stream
        let newResponse: JQuery<HTMLElement> = $("#response_stream");
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

export default ChatLogic