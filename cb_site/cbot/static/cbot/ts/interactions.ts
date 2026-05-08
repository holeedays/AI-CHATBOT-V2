import { StaticReferences as sr } from "./static_references.ts"

// scroll down if need be
export function scroll(scrollDuration: number): void {
    $("html, body").stop().animate({
        scrollTop: $(document).height()
    }, scrollDuration);

}

// allows our input area to dynamically expand
export function allowDynamicInputArea(inputArea: JQuery<HTMLElement>): void {
    inputArea.on("input", (event: JQuery.TriggeredEvent) => {
        const element: HTMLElement = event.currentTarget as HTMLElement;
        $(element).css("height", "auto");
        $(element).css("height", element.scrollHeight + "px");
    });
}

// check for enterkey
export function initializeEnterKey(callback: ()=> void): void {
    $(document).on("keydown", (event: JQuery.KeyDownEvent) => {
        // allows for dynamic resizing much like other chat bots
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            callback();
        }
    });        
}

// font switching functionalities
export function initializeFontSwitchButton(fontSwitchButton: JQuery<HTMLElement>): void {
    const label: JQuery<HTMLElement> = $(sr.SPAN_BLOCK)
        .addClass("font_switch_label")
        .text(sr.FONT_SWITCH_LABEL_OFF);
    const track: JQuery<HTMLElement> = $(sr.SPAN_BLOCK).addClass("font_switch_track");
    const thumb: JQuery<HTMLElement> = $(sr.SPAN_BLOCK).addClass("font_switch_thumb");

    track.append(thumb);
    fontSwitchButton.empty().append(label, track);
    const isPlainFont: boolean = $("body").hasClass(sr.FONT_SWITCH_PLAIN_CLASS);
    setFontSwitchState(fontSwitchButton, isPlainFont);

    fontSwitchButton.on("click", () => {
        // switch the values on the front end
        const isActive: boolean = fontSwitchButton.hasClass(sr.FONT_SWITCH_ACTIVE_CLASS);
        const nextState: boolean = !isActive;
        setFontSwitchState(fontSwitchButton, nextState);
        const csrfToken: string = $('meta[name="csrf-token"]').attr("content") ?? "";

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
export function setFontSwitchState(fontSwitchButton: JQuery<HTMLElement>, isPlainFont: boolean): void {
    $("body").toggleClass(sr.FONT_SWITCH_PLAIN_CLASS, isPlainFont);
    fontSwitchButton.toggleClass(sr.FONT_SWITCH_ACTIVE_CLASS, isPlainFont);
    fontSwitchButton.attr("aria-pressed", String(isPlainFont));

    const labelText: string = isPlainFont ? sr.FONT_SWITCH_LABEL_ON : sr.FONT_SWITCH_LABEL_OFF;
    fontSwitchButton.find(".font_switch_label").text(labelText);
}

// Give new or updated chat content a light ease-in without changing the layout.
export function easeInElement(element: JQuery<HTMLElement>, durationMS: number = 180): void {
    element.stop(true, true);
    element.css("opacity", "0.25");
    element.animate({ opacity: 1 }, durationMS, "swing");
}
