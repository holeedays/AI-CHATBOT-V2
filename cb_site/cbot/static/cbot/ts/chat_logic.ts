declare const marked: any;

class ChatLogic {

    private inputArea: JQuery<HTMLInputElement>;
    private chatWindow: JQuery<HTMLDivElement>;
    private submitButton: JQuery<HTMLButtonElement>;

    private awaitingResponse: boolean;
    private ignoringStrayChunks: boolean;

    private ws: WebSocket;

    
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
        this.awaitingResponse = false;
        this.ignoringStrayChunks = false;
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

        this.ws.onerror = (ev: Event) => {console.error("WebSocket error:", ev)};
    }

    // check for enterkey
    private initializeEnterKey(): void {
        $(document).on("keydown", (event: JQuery.KeyDownEvent) => {
            if (event.key === "Enter")
                this.onSubmit();
        });        
    }

    // our callback when user submits a request
    private async onSubmit(): Promise<void> {
        // btw, we use .val() instead of .text() for input html elements
        const message: string | undefined = this.inputArea.val();

        if (message === undefined) {
            console.warn("Message is undefined, doing nothing");
            return;
        }

        // add the user to the window chat
        const trimmedMessage: string = message.trim();
        if (trimmedMessage.length === 0)
            return;
        // create a new object and edit it this way so that the user can't just add raw html
        // to our page
        const userInput = $("<p></p>").addClass("user_input");
        userInput.append($("<strong></strong>").text("User:"));
        userInput.append(document.createTextNode(` ${trimmedMessage}`));
        this.chatWindow.append(userInput);
        
        // clear our input area
        this.inputArea.val("");
        
        // await for a successful reset
        await this.reset();

        // also start generating some queuing text to keep the person occupied
        const timeBetweenPhraseMS: number = 4000;
        this.generateQueuingText(timeBetweenPhraseMS);

        // send our message
        const input_JSON: string = JSON.stringify({
            "message": trimmedMessage
        });

        this.ws.send(input_JSON);
    }

    // reset existing processes (used in onSubmit as a clear all thing)
    private async reset(): Promise<void> {
        // remove the existing response if it exists
        const existing_stream: JQuery<HTMLElement> = $("#response_stream");
        if (existing_stream.length != 0) {
            existing_stream.removeAttr("id");
            existing_stream.addClass("completed_response");
        }
    }

    // callback when our websocket gets a response (partial or full)
    private async onResponse(ev: MessageEvent): Promise<void> {
        if (this.ignoringStrayChunks) {
            console.log("Deflected a stray chunk");
            return;
        }

        this.awaitingResponse = false;
        // Wait for queuing text to disappear
        while ($("#queuing").length !== 0) {
            await new Promise((res) => setTimeout(res, 50));
        }
        
        // find our new response stream
        let newResponse: JQuery<HTMLElement> = $("#response_stream");
        // check if it exists, if not, add the element
        if (newResponse.length === 0) {
            this.chatWindow.append(`
                <pre>
                    <div id="response_stream">
                    </div>
                </pre>
            `);
            newResponse = $("#response_stream");
        }

        // actually get our response
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

        const htmlContent = marked.parse(responseBody) as string;
        
        // Update our response stream with the new content
        newResponse.html(`<strong>AIB:</strong> ${htmlContent}`);

        // also check if response is finished
        if (responseFinished) {
            newResponse.removeAttr("id");
            newResponse.addClass("completed_response");

            const deflectionTimeMS: number = 500;
            this.ignoringStrayChunks = true;
            setTimeout(() => {
                this.ignoringStrayChunks = false;
            }, deflectionTimeMS);
        }
    }

    // generate some text to keep the person occupied as a response is being generated
    private async generateQueuingText(timeBetweenPhrasesMS: number) {
        this.awaitingResponse = true;

        let queuingText: JQuery<HTMLElement> = $("#queuing");
        if (queuingText.length === 0) {
            this.chatWindow.append(`
                <p id="queuing"> 
                    <strong>AIB:</strong>
                </p>
            `);
            queuingText = $("#queuing");
        }

        const queuingTextPhrases: [string[], string[], string[], string[], string[]] = [
            ["Parsing request intent...", "Just reading through that now...", "Reviewing your request...", "Understanding your goal..."],
            ["Scanning internal knowledge base...", "Gathering all the relevant facts.", "Gathering the facts.", "Searching for the best info."],
            ["Evaluating multi-step logic...", "Looking for patterns...", "Connecting the ideas.", "Organzing the details."],
            ["Drafting the response...", "Putting it all together.", "Defining your response.", "Creating your answer."],
            ["Finalizing output formatting...", "Almost there... Adding final touches...", "Adding the final touches.", "Checking for accuracy."]
        ]
        let currentPhraseIndex: number = -1;

        while(this.awaitingResponse) {
            const currentAvailablePhrases: string[] = queuingTextPhrases[currentPhraseIndex] ?? [];
            const randomIndex: number = Math.floor(Math.random() * currentAvailablePhrases.length);
            const textPhrase: string = currentAvailablePhrases[randomIndex] ?? ""; 
            
            queuingText.html(`<strong>AIB:</strong> ${textPhrase}`);

            await new Promise((res) => setTimeout(res, timeBetweenPhrasesMS));
            // cap current phrase index so it stays on the last stage if the response takes a long time
            if (currentPhraseIndex < queuingTextPhrases.length - 1) {
                currentPhraseIndex++;
            }
        }
        
        queuingText.remove();
    }
}

export default ChatLogic