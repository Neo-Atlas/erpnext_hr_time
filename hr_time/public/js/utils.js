export class NumberCardUtils {
    /**
     * Adjusts the block and header style of a number card
     */
    static adjust_block_style(card_name) {
        document.querySelector('[number_card_name="' + card_name + '"]')
            .querySelector(".widget-content")
            .setAttribute("style", "display: block; padding-top: 15px;");
    }
}