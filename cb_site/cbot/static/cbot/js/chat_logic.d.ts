declare class ChatLogic {
    private inputArea;
    private chatWindow;
    private submitButton;
    private awaitingResponse;
    private ws;
    constructor();
    private initializeSubmitButton;
    private initializeWebsocket;
    private initializeEnterKey;
    private onSubmit;
    private reset;
    private onResponse;
    private generateQueuingText;
}
export default ChatLogic;
//# sourceMappingURL=chat_logic.d.ts.map