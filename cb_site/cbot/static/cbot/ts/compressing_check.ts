class CompressionCheck {
    private readonly statusUrl: string;
    private readonly chatUrl: string;
    private readonly statusText: JQuery<HTMLElement>;
    private readonly statusMessages: string[];

    private currentMessageIndex: number;

    constructor() {
        this.statusUrl = $("body").data("status-url") as string;
        this.chatUrl = $("body").data("chat-url") as string;
        this.statusText = $("#compression_status_text");
        this.statusMessages = [
            "Saving your previous conversation...",
            "Compressing the earlier context...",
            "Tidying the session before reopening chat...",
            "Almost done getting things ready again..."
        ];

        this.currentMessageIndex = 0;

        this.initializeStatusMessage();
        const messageIntervalMS: number = 3000;
        this.startMessageCycle(messageIntervalMS);
        this.checkCompressionStatus();
    }

    // Set the first message immediately so the view is never blank.
    private initializeStatusMessage(): void {
        this.statusText.text(this.statusMessages[this.currentMessageIndex] ?? "Please wait a moment.");
    }

    // Rotate through the loading messages with a simple fade transition.
    private startMessageCycle(intervalMS: number): void {
        window.setInterval(() => {
            this.currentMessageIndex = (this.currentMessageIndex + 1) % this.statusMessages.length;
            const nextMessage: string = this.statusMessages[this.currentMessageIndex] ?? "Please wait a moment.";

            this.statusText.stop(true, true).fadeOut(250, "swing", () => {
                this.statusText.text(nextMessage).fadeIn(250, "swing");
            });
        }, intervalMS);
    }

    // Poll the server until context compression is finished, then return to chat.
    private checkCompressionStatus(): void {
        $.ajax({
            url: this.statusUrl,
            method: "GET",
            cache: false,
            dataType: "json",
            success: (payload: { is_compressing_context?: boolean }) => {
                if (payload.is_compressing_context === false) {
                    window.location.replace(this.chatUrl);
                    return;
                }

                window.setTimeout(() => this.checkCompressionStatus(), 1000);
            },
            error: () => {
                window.setTimeout(() => this.checkCompressionStatus(), 1500);
            }
        });
    }
}

$(function () {
    new CompressionCheck();
});
