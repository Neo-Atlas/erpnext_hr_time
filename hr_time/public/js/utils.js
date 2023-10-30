export class NumberCardUtils {
    static adjust_block_style(div_id) {
        document.getElementById(div_id)
            .parentElement
            .parentElement
            .setAttribute("style", "display: block; padding-top: 15px;");
    }
}