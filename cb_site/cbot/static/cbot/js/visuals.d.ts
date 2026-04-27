declare class TextTyper {
    queue: Promise<void>;
    constructor();
    type(htmlElem: JQuery<HTMLElement>, targetText: string, timeSpanMS: number): void;
    addToQueue(task: () => Promise<void>): void;
    typeText(htmlElem: JQuery<HTMLElement>, targetText: string, timeSpanMS: number): Promise<void>;
}
export default TextTyper;
//# sourceMappingURL=visuals.d.ts.map