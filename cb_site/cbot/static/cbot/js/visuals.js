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
var TextFunctionalities;
(function (TextFunctionalities) {
    // essentially an enum for possible typing styles
    class TypingStyles {
        static BY_LETTER = "by_letter";
        static BY_WORD = "by_word";
    }
    // the class responsible for actuall typing text in our website
    class TextTyper {
        queue;
        constructor() {
            // init an empty queue so we can chain other async functions
            this.queue = Promise.resolve();
        }
        type(htmlElem, targetText, typeStyle, timeSpanMS) {
            switch (typeStyle) {
                case (TypingStyles.BY_LETTER):
                    this.addToQueue(() => this.typeTextByLetter(htmlElem, targetText, timeSpanMS));
                    break;
                case (TypingStyles.BY_WORD):
                    this.addToQueue(() => this.typeTextByWord(htmlElem, targetText, timeSpanMS));
                    break;
            }
        }
        addToQueue(task) {
            this.queue = this.queue.then(task);
        }
        // typing text by letter version (this one is suitable for openAI chunk streams)
        async typeTextByLetter(htmlElem, targetText, timeSpanMS) {
            const charArray = targetText.split(" ");
            const arrLength = charArray.length;
            // this returns infinity when the string is empty, so just skip entirely
            if (arrLength === Infinity)
                return;
            // just in case timing is not truly perfect, I included a small reduction in the input
            // though it should be noted setTimeouts (nested ones) are hardcapped at 4 ms 
            // while synchronous ones can be as quick as .2 ms
            const timeErrorMS = 5;
            // iterate through our char array 
            for (const char of charArray) {
                htmlElem.append(char);
                await new Promise((res) => { setTimeout(res, (timeSpanMS - timeErrorMS) / arrLength); });
            }
            ;
        }
        // typing text by word version (this one is suitable for gemini chunk streams)
        async typeTextByWord(htmlElem, targetText, timeSpanMS) {
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
})(TextFunctionalities || (TextFunctionalities = {}));
export default TextFunctionalities;
//# sourceMappingURL=visuals.js.map