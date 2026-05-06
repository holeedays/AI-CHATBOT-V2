export class StaticReferences {
    public static readonly JQUERY_QUEUE_TEXT: string = "#queue" 
    public static readonly JQUERY_RESPONSE_STREAM: string = "#response_stream"

    public static readonly RESPONSE_TEMPLATE: string = `<pre>
                                                            <div id=${this.JQUERY_RESPONSE_STREAM}>
                                                            <div>        
                                                        <pre>        
                                                        `

    public static readonly COMPLETED_RESPONSE: string = "completed_response"
    public static readonly USER_INPUT: string = "user_input"
}