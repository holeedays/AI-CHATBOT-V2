import { StaticReferences as sr } from "./static_references.js";
// scroll down if need be
export function scroll(scrollDuration) {
    $("html, body").stop().animate({
        scrollTop: $(document).height()
    }, scrollDuration);
}
// allows our input area to dynamically expand
export function allowDynamicInputArea(inputArea) {
    inputArea.on("input", (event) => {
        const element = event.currentTarget;
        $(element).css("height", "auto");
        $(element).css("height", element.scrollHeight + "px");
    });
}
// check for enterkey
export function initializeEnterKey(callback) {
    $(document).on("keydown", (event) => {
        // allows for dynamic resizing much like other chat bots
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            callback();
        }
    });
}
// font switching functionalities
export function initializeFontSwitchButton(fontSwitchButton) {
    const label = $(sr.SPAN_BLOCK)
        .addClass("font_switch_label")
        .text(sr.FONT_SWITCH_LABEL_OFF);
    const track = $(sr.SPAN_BLOCK).addClass("font_switch_track");
    const thumb = $(sr.SPAN_BLOCK).addClass("font_switch_thumb");
    track.append(thumb);
    fontSwitchButton.empty().append(label, track);
    const isPlainFont = $("body").hasClass(sr.FONT_SWITCH_PLAIN_CLASS);
    setFontSwitchState(fontSwitchButton, isPlainFont);
    fontSwitchButton.on("click", () => {
        // switch the values on the front end
        const isActive = fontSwitchButton.hasClass(sr.FONT_SWITCH_ACTIVE_CLASS);
        const nextState = !isActive;
        setFontSwitchState(fontSwitchButton, nextState);
        const csrfToken = $('meta[name="csrf-token"]').attr("content") ?? "";
        // save our preference here to the db
        $.ajax({
            url: "/font-preference/",
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
            },
            data: {
                use_plain_font: String(nextState),
            },
        });
    });
}
// subsidiary helper method to the initializeFontSwitch one
export function setFontSwitchState(fontSwitchButton, isPlainFont) {
    $("body").toggleClass(sr.FONT_SWITCH_PLAIN_CLASS, isPlainFont);
    fontSwitchButton.toggleClass(sr.FONT_SWITCH_ACTIVE_CLASS, isPlainFont);
    fontSwitchButton.attr("aria-pressed", String(isPlainFont));
    const labelText = isPlainFont ? sr.FONT_SWITCH_LABEL_ON : sr.FONT_SWITCH_LABEL_OFF;
    fontSwitchButton.find(".font_switch_label").text(labelText);
}
// Give new or updated chat content a light ease-in without changing the layout.
export function easeInElement(element, durationMS = 180) {
    element.stop(true, true);
    element.css("opacity", "0.25");
    element.animate({ opacity: 1 }, durationMS, "swing");
}
//# sourceMappingURL=interactions.js.map