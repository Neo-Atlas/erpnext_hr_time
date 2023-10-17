frappe.listview_settings['Flextime daily status'] = {

    options: {
        columns: ["flextime_delta"]
    },

    // set this to true to apply indicator function on draft documents too
    has_indicator_for_draft: false,

    onload(listview) {
        console.log(listview);
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
    }
}