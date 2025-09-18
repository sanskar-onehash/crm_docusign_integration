// Copyright (c) 2025, OneHash and contributors
// For license information, please see license.txt

frappe.ui.form.on("DocuSign Integration", {
  provide_consent: async function (frm) {
    if (frm.is_dirty()) {
      frappe.msgprint("Please save the changes before providing the consent.");
      return;
    }

    await frm.set_value("is_verified", false);
    await frm.save();
    frm.set_df_property("provide_consent", "hidden", 1);
    frappe.show_alert(
      {
        message: "DocuSign consent process initiated",
        indicator: "blue",
      },
      5,
    );

    frappe.call({
      method: "crm_docusign_integration.docusign.integration.auth.get_consent_url",
      callback: (r) => r.message && (window.location.href = r.message),
    });
  },
});
