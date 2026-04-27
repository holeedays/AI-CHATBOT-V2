// async function typeText(htmlElem: JQuery<HTMLElement>, targetText: string, timeSpanMS: number): Promise<void> {
//     // don't know how effective for long chunks of text, but this should be A okay for now
//     const textArray: string[] = targetText.split("");
//     const arrLength = textArray.length;
//     // just in case timing is not truly perfect, I included a small delay
//     const timeErrorMS = 10;
//     // iterate through our text array 
//     for (const char of textArray) {
//         htmlElem.append(char);
//         await new Promise((res) => {setTimeout(res, (timeSpanMS - timeErrorMS)/arrLength)})
//     };
// }
class TextTyper {
    queue;
    constructor() {
        // init an empty queue so we can chain other async functions
        this.queue = Promise.resolve();
    }
    type(htmlElem, targetText, timeSpanMS) {
        this.addToQueue(() => this.typeText(htmlElem, targetText, timeSpanMS));
    }
    addToQueue(task) {
        this.queue = this.queue.then(task);
    }
    async typeText(htmlElem, targetText, timeSpanMS) {
        // don't know how effective for long chunks of text, but this should be A okay for now
        const textArray = targetText.split(" ");
        const arrLength = textArray.length;
        // this returns infinity when the string is empty, so just skip entirely
        if (arrLength === Infinity)
            return;
        // just in case timing is not truly perfect, I included a small reduction in the input
        // though it should be noted setTimeouts (nested ones) are hardcapped at 4 ms 
        // while synchronous ones can be as quick as .2 ms
        const timeErrorMS = 5;
        // iterate through our text array 
        for (const word of textArray) {
            htmlElem.append(" " + word);
            await new Promise((res) => { setTimeout(res, (timeSpanMS - timeErrorMS) / arrLength); });
        }
        ;
    }
}
export default TextTyper;
//# sourceMappingURL=visuals.js.map