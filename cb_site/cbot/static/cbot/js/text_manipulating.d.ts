export declare namespace TypingFunctionalities {
    enum TypingStyles {
        BY_LETTER = 0,
        BY_WORD = 1
    }
    enum QueueState {
        ADDING = 0,// signifies currently adding stuff to the queue
        FINISHING = 1,// signifies nothing else will be added to the queue
        QUITTING = 2
    }
    class TextTyper {
        queue: Promise<void>;
        queueState: QueueState;
        constructor();
        type(htmlElem: JQuery<HTMLElement>, targetText: string, typeStyle: TypingStyles, pauseTimeMS: number): void;
        private addToQueue;
        finish(): void;
        reset(): Promise<void>;
        typeTextByLetter(htmlElem: JQuery<HTMLElement>, targetText: string, pauseTimeMS: number): Promise<void>;
        typeTextByWord(htmlElem: JQuery<HTMLElement>, targetText: string, pauseTimeMS: number): Promise<void>;
    }
}
//# sourceMappingURL=text_manipulating.d.ts.map