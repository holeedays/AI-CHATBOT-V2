export declare namespace TextModifiers {
    class TextParser {
        private dp;
        constructor();
        insertItemsBeforeAfterSelector(html: string, htmlSelector: string, insertElement: string): string;
        parseMarkdown(text: string): Promise<string>;
    }
}
//# sourceMappingURL=text_modifiers.d.ts.map