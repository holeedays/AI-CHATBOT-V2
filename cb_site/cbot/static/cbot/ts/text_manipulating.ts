// though this is somewhat discouraged (individual modules are preferred in ts)
// I'll stick with a namespace for this specifically
export namespace TypingFunctionalities {
    // typing styles, used to determine the appropriate methods in class text typer
    export enum TypingStyles {
        BY_LETTER,
        BY_WORD
    }
    // determines the queue state of a promise chain
    export enum QueueState {
        ADDING, // signifies currently adding stuff to the queue
        FINISHING, // signifies nothing else will be added to the queue
        QUITTING // signifies an abrupt exit of the current queue
    }

    // the class responsible for actuall typing text in our website
    export class TextTyper {
        public queue: Promise<void>;
        public queueState: QueueState;

        constructor() {
            // init an empty queue so we can chain other async functions
            this.queue = Promise.resolve();
            this.queueState = QueueState.FINISHING;
        }

        // logical wrapper for typing text 
        public type(htmlElem: JQuery<HTMLElement>, targetText: string, typeStyle: TypingStyles, pauseTimeMS: number) {
            switch(typeStyle){
                case (TypingStyles.BY_LETTER):
                    this.addToQueue(() => this.typeTextByLetter(htmlElem, targetText, pauseTimeMS));
                    break;

                case (TypingStyles.BY_WORD):
                    this.addToQueue(() => this.typeTextByWord(htmlElem, targetText, pauseTimeMS));
                    break;
            }
        }

        // add a task to queue
        private addToQueue(task: () => Promise<void>): void {
            this.queue = this.queue.then(async() => {
                this.queueState = QueueState.ADDING;
                await task();
            });
        }

        // just a signifier to typing text indicating that the queue is done and nothing else will be queued
        public finish(): void {
            this.queue = this.queue.finally(() => {
                this.queueState = QueueState.FINISHING;
            });
        }

        // the idea is there'll be some condition in all of the queued tasks, which, when accessed will kill the 
        // entire chain on the next task

        // simplified wrapper for resetting the text typer state 
        public async reset(): Promise<void> {
            // this whole part is dedicated to ending the current promise chain; it is required that the this
            // method is used in an async method to work properly
            if (this.queueState !== QueueState.ADDING) 
                return;

            // add to the end of the promise chain an error catcher so every chain that throws an console.error
            // will automatically move to end of the queue
            this.queueState = QueueState.QUITTING;
            this.queue = this.queue.catch((err) => {
                console.warn(err);
                this.queueState = QueueState.FINISHING;
                // reset queue, so we can chain further resolves after the rejection statement
                this.queue = Promise.resolve();
            });

            // arbitrary time check for checking when our queue encounters the error catch
            const timeCheckRateMs: number = 250;
            while (this.queueState === QueueState.QUITTING) {
                await new Promise<void>((res) => {
                    setTimeout(res, timeCheckRateMs)
                });
            }
        }

        // typing text by letter version (this one is suitable for openAI chunk streams)
        public async typeTextByLetter(htmlElem: JQuery<HTMLElement>, targetText: string, pauseTimeMS: number): Promise<void> {
            const charArray: string[] = targetText.split("") 
            const arrLength = charArray.length;

            // this returns infinity when the string is empty, so just skip entirely
            if (arrLength === Infinity)
                return;

            // iterate through our char array 
            for (const char of charArray) {
                if (this.queueState === QueueState.QUITTING)
                    throw new Error("QUIT_CURRENT_QUEUE");
                htmlElem.append(char);
                // note, setTimeout can be as short as 0.2 ms but in standard it is capped at 4 ms
                await new Promise<void>((res) => {setTimeout(res, (pauseTimeMS)/arrLength)});

            };
        } 

        // typing text by word version (this one is suitable for gemini chunk streams)
        public async typeTextByWord(htmlElem: JQuery<HTMLElement>, targetText: string, pauseTimeMS: number): Promise<void> {
            const textArray: string[] = targetText.split(" ") 
            const arrLength = textArray.length;

            // this returns infinity when the string is empty, so just skip entirely
            if (arrLength === Infinity)
                return;

            // iterate through our text array 
            for (const word of textArray) {
                if (this.queueState === QueueState.QUITTING)
                    throw new Error("QUIT_CURRENT_QUEUE");
                // null operator check in case htmlElem.text does not exist
                htmlElem.append((htmlElem.text()?.length ?? 0) === 0 ? word : " " + word);
                await new Promise<void>((res) => {setTimeout(res, (pauseTimeMS)/arrLength)});
            };
        }
    }
}




