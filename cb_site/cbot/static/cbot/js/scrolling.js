function scroll(container) {
    parent.scrollTop();
}
// check for enterkey
function initializeEnterKey(callback) {
    $(document).on("keydown", (event) => {
        if (event.key === "Enter")
            callback();
    });
}
export {};
//# sourceMappingURL=scrolling.js.map