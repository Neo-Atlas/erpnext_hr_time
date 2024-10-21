// Copyright (c) 2023, AtlasAero GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Flextime daily status", {
  validate: function (form) {
    if (form.doc.total_working_hours === "") {
      form.doc.total_working_hours = 0;
    }
  },
});
