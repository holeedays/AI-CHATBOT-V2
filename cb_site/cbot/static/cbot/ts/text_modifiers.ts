// import { marked } from "Marked"

declare const marked: {
    parse(text: string): string | Promise<string>;
};

export namespace TextModifiers {

    export class TextParser {
        private dp: DOMParser;

        constructor() {
            this.dp = new DOMParser();
        }

        // insert some html element before and after another html element
        public insertItemsBeforeAfterSelector(html: string, htmlSelector: string, insertElement: string): string {   
            // parse the html string 
            const document: Document = this.dp.parseFromString(html, "text/html");
            // select the elements we want to target in our newly created document
            const elementNodes: NodeListOf<Element> = document.querySelectorAll(htmlSelector);

            // iterate through our elements, and add in our insert element to the back and front
            for (const elementNode of elementNodes) {

                // I have to cast here to access before/after/previousElementSibling/etc because node holds only
                // raw text while 
                const parentNode: Element | null = elementNode.parentNode as Element;

                const insertPrefix: HTMLElement = document.createElement(insertElement);
                const insertSuffix: HTMLElement = document.createElement(insertElement);

                // we're checking parent too b/c siblings have to be in the same parent which is not what we want
                // to determine sometimes
                const elemPrevTag: string | undefined = elementNode.previousElementSibling?.tagName.toLowerCase();
                const elemNextTag: string | undefined = elementNode.nextElementSibling?.tagName.toLowerCase();
                const parentElemPrevTag: string | undefined = parentNode?.previousElementSibling?.tagName.toLowerCase();
                const parentElemNextTag: string | undefined = parentNode?.nextElementSibling?.tagName.toLowerCase();
                

                if (elemPrevTag !== insertElement.toLowerCase() ||
                    parentElemPrevTag !== insertElement.toLowerCase()) {
                    elementNode.before(insertPrefix);
                }

                if (elemNextTag !== insertElement.toLowerCase() ||
                    parentElemNextTag !== insertElement.toLowerCase()) {
                    elementNode.after(insertSuffix);
                }
            }

            // return this edited html
            return document.body.innerHTML;
        }

        // parse any output from markdown while also correcting some errors during conversion
        public async parseMarkdown(text: string): Promise<string> {
            let parsedText: string = await marked.parse(text);
            parsedText = this.insertItemsBeforeAfterSelector(parsedText, "img", "br");

            return parsedText;
        }
    }


}
