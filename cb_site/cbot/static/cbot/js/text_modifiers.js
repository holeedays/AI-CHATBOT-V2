// import { marked } from "Marked"
export var TextModifiers;
(function (TextModifiers) {
    class TextParser {
        dp;
        constructor() {
            this.dp = new DOMParser();
        }
        // insert some html element before and after another html element
        insertItemsBeforeAfterSelector(html, htmlSelector, insertElement) {
            // parse the html string 
            const document = this.dp.parseFromString(html, "text/html");
            // select the elements we want to target in our newly created document
            const elementNodes = document.querySelectorAll(htmlSelector);
            // iterate through our elements, and add in our insert element to the back and front
            for (const elementNode of elementNodes) {
                // I have to cast here to access before/after/previousElementSibling/etc because node holds only
                // raw text while 
                const parentNode = elementNode.parentNode;
                const insertPrefix = document.createElement(insertElement);
                const insertSuffix = document.createElement(insertElement);
                // we're checking parent too b/c siblings have to be in the same parent which is not what we want
                // to determine sometimes
                const elemPrevTag = elementNode.previousElementSibling?.tagName.toLowerCase();
                const elemNextTag = elementNode.nextElementSibling?.tagName.toLowerCase();
                const parentElemPrevTag = parentNode?.previousElementSibling?.tagName.toLowerCase();
                const parentElemNextTag = parentNode?.nextElementSibling?.tagName.toLowerCase();
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
        async parseMarkdown(text) {
            let parsedText = await marked.parse(text);
            parsedText = this.insertItemsBeforeAfterSelector(parsedText, "img", "br");
            return parsedText;
        }
    }
    TextModifiers.TextParser = TextParser;
})(TextModifiers || (TextModifiers = {}));
//# sourceMappingURL=text_modifiers.js.map