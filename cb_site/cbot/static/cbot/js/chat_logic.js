import { StaticReferences as sr } from "./static_references.js";
import { allowDynamicInputArea, initializeEnterKey, initializeFontSwitchButton, easeInElement, scroll } from "./interactions.js";
import { TextModifiers } from "./text_modifiers.js";
class ChatLogic {
    inputArea;
    chatWindow;
    submitButton;
    fontSwitchButton;
    awaitingResponse;
    processingQueue;
    messageQueue;
    ws;
    tp;
    constructor() {
        // get all HTML elements
        this.inputArea = $(sr.JQUERY_USER_INPUT_AREA_ID);
        this.chatWindow = $(sr.JQUERY_CHAT_WINDOW_ID);
        this.submitButton = $(sr.JQUERY_SUBMIT_BUTTON_ID);
        this.fontSwitchButton = $(sr.JQUERY_FONT_SWITCH_BUTTON_ID);
        this.initializeSubmitButton();
        initializeFontSwitchButton(this.fontSwitchButton);
        initializeEnterKey(() => this.onSubmit());
        allowDynamicInputArea(this.inputArea);
        // establish websocket connection
        // first determine header of connection 
        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        // append that to get our string (the last part should be reflected in our routing.py)
        const socketURL = `${protocol}${window.location.host}/ws/response_stream/`;
        // then initialize it and its functions
        this.ws = new WebSocket(socketURL);
        this.initializeWebsocket();
        // other classes for better functionalities
        this.tp = new TextModifiers.TextParser();
        // misc
        this.awaitingResponse = false;
        this.processingQueue = false;
        this.messageQueue = [];
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
    // our callback when user submits a request
    onSubmit() {
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
        // update the UI for the user
        this.updateChatWindowUser(trimmedMessage);
        this.resetInputArea();
        // await for a successful reset
        this.reset();
        // also start generating some queuing text to keep the person occupied
        const timeBetweenPhraseMS = 4000;
        this.generateQueuingText(timeBetweenPhraseMS);
        // send our message
        const input_JSON = JSON.stringify({
            "message": trimmedMessage
        });
        this.ws.send(input_JSON);
    }
    // reset existing processes (used in onSubmit as a clear all thing)
    reset() {
        // remove the existing response if it exists
        const existing_stream = $(sr.JQUERY_RESPONSE_STREAM_ID);
        if (existing_stream.length != 0) {
            existing_stream.removeAttr(sr.JQUERY_ID);
            existing_stream.addClass(sr.COMPLETED_RESPONSE);
        }
        // remove the queuing text block if it exists
        this.removeQueuingText();
    }
    // callback when our websocket gets a response (partial or full)
    async onResponse(ev) {
        // this acts like a synchronous queue, forcing each packet of our event data to be synchronized rather 
        // than running rampant with parallel operations (which can cause our response stream to conclude earlier
        // than necessary — which causes duplicates which are not good)
        this.messageQueue.push(ev);
        if (this.processingQueue)
            return;
        this.processingQueue = true;
        while (this.messageQueue.length > 0) {
            const currentEv = this.messageQueue.shift();
            if (currentEv !== undefined)
                await this.handleResponse(currentEv);
        }
        this.processingQueue = false;
    }
    // this is where we actually execute our response cold
    async handleResponse(ev) {
        this.awaitingResponse = false;
        // Wait for queuing text to disappear
        while ($(sr.JQUERY_QUEUE_TEXT_CONTAINER_ID).length !== 0) {
            await new Promise((res) => setTimeout(res, 50));
        }
        // actually get our response
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
        // now handle the UI logic 
        await this.updateChatWindowResponse(responseBody, responseFinished);
    }
    // generate some text to keep the person occupied as a response is being generated
    async generateQueuingText(timeBetweenPhrasesMS) {
        this.awaitingResponse = true;
        let queuingText = $(sr.JQUERY_QUEUE_TEXT_CONTAINER_ID);
        if (queuingText.length === 0) {
            this.chatWindow.append(sr.QUEUING_TEXT_TEMPLATE);
            queuingText = $(sr.JQUERY_QUEUE_TEXT_CONTAINER_ID);
        }
        // this holds the actual text, it is created during our template
        const queuingMessage = $(sr.JQUERY_QUEUE_TEXT_MESSAGE_ID);
        let currentPhraseIndex = 0;
        while (this.awaitingResponse) {
            const currentAvailablePhrases = sr.QUEUING_TEXT_PHRASES[currentPhraseIndex] ?? [];
            const randomIndex = Math.floor(Math.random() * currentAvailablePhrases.length);
            const textPhrase = currentAvailablePhrases[randomIndex] ?? "";
            queuingMessage.text(textPhrase);
            const scroll_duraton = 300;
            scroll(scroll_duraton);
            await new Promise((res) => setTimeout(res, timeBetweenPhrasesMS));
            // cap current phrase index so it stays on the last stage if the response takes a long time
            if (currentPhraseIndex < sr.QUEUING_TEXT_PHRASES.length - 1) {
                currentPhraseIndex++;
            }
        }
        queuingText.remove();
    }
    // removes the queuing text block
    removeQueuingText() {
        const queuingText = $(sr.JQUERY_QUEUE_TEXT_CONTAINER_ID).parent(sr.PRE_SELECTOR_TAG);
        if (queuingText.length > 0) {
            queuingText.remove();
        }
    }
    // fix back the dimensions of our input area
    resetInputArea() {
        this.inputArea.css("height", "auto");
    }
    // update the UI for our user in the chat window 
    updateChatWindowUser(trimmedMessage) {
        // create a new object and edit it this way so that the user can't just add raw html
        // to our page
        const container = $(sr.PRE_BLOCK).addClass(sr.USER_INPUT_WRAPPER);
        const actualContents = $(sr.DIV_BLOCK).css("opacity", "0.7");
        container.append(actualContents.addClass(sr.COMPLETED_RESPONSE));
        actualContents.append($(sr.STRONG_BLOCK).text(sr.USER_HEADER));
        actualContents.append($(sr.PARAGRAPH_BLOCK).text(`${trimmedMessage}`));
        this.chatWindow.append(container);
        easeInElement(actualContents);
        const scrollSpeed = 300;
        scroll(scrollSpeed);
        // clear our input area
        this.inputArea.val("");
    }
    async updateChatWindowResponse(responseBody, responseFinished) {
        // find our new response stream
        let newResponse = $(sr.JQUERY_RESPONSE_STREAM_ID);
        let isNewResponse = false;
        // check if it exists, if not, add the element
        if (newResponse.length === 0) {
            const container = $(sr.RESPONSE_TEMPLATE)
                .addClass(sr.AI_RESPONSE_WRAPPER)
                .css("opacity", "0.7");
            this.chatWindow.append(container);
            newResponse = $(sr.JQUERY_RESPONSE_STREAM_ID);
            isNewResponse = true;
        }
        const htmlContent = await this.tp.parseMarkdown(responseBody);
        // Update our response stream with the new content
        newResponse.html(`${sr.AI_HEADER_STRONG} ${htmlContent}`);
        // Make it a little flashy
        easeInElement(isNewResponse ? newResponse.parent(sr.PRE_SELECTOR_TAG) : newResponse);
        const scrollSpeed = 300;
        scroll(scrollSpeed);
        // also check if response is finished
        if (responseFinished) {
            newResponse.removeAttr(sr.JQUERY_ID);
            newResponse.addClass(sr.COMPLETED_RESPONSE);
        }
    }
}
export default ChatLogic;
//# sourceMappingURL=chat_logic.js.map