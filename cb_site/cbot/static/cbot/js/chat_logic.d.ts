declare class ChatLogic {
    private inputArea;
    private chatWindow;
    private submitButton;
    private fontSwitchButton;
    private awaitingResponse;
    private processingQueue;
    private messageQueue;
    private ws;
    private tp;
    constructor();
    private initializeSubmitButton;
    private initializeWebsocket;
    private onSubmit;
    private reset;
    private onResponse;
    private handleResponse;
    private generateQueuingText;
    private removeQueuingText;
    private resetInputArea;
    private updateChatWindowUser;
    private updateChatWindowResponse;
}
export default ChatLogic;
//# sourceMappingURL=chat_logic.d.ts.map