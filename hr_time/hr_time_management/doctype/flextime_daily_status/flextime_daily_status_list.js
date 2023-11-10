frappe.listview_settings['Flextime daily status'] = {
    add_fields: ["target_working_time"],

    options: {
        columns: ["flextime_delta"]
    },

    // set this to true to apply indicator function on draft documents too
    has_indicator_for_draft: false,

    refresh(view) {
        $("a[data-doctype=\"Employee\"]").each(function () {
            let element = $(this);
            let text = element.html();

            if (!text.includes(":")) {
                return;
            }

            element.html(text.split(":")[0]);
        })
    },

    onload(view) {
        this.hide_sidebar();
    },

    before_render() {
        this.hide_sidebar();
    },

    get_indicator(doc) {
        if ((doc.target_working_time === 0 || doc.target_working_time === undefined) && doc.total_working_hours === 0) {
            return [__("No workday"), "grey", "target_working_time,=,0"];
        }

        if (doc.flextime_delta === 0) {
            return [__("Neutral"), "blue", "flextime_delta,=,0"];
        }

        if (doc.flextime_delta > 0) {
            return [__("Time gain"), "green", "flextime_delta,>,0"];
        }

        if (doc.flextime_delta < 0) {
            return [__("Time loss"), "red", "flextime_delta,<,0"];
        }
    },

    hide_sidebar() {
        console.log("Called!");

        if ($(".list-sidebar.overlay-sidebar").is(":visible")) {
            $("span.sidebar-toggle-btn").click();
        }
    }
}