frappe.listview_settings["Document Template"] = {
  onload: function (listview) {
    addDocumentTemplateListActions(listview);
  },
};

function addDocumentTemplateListActions(listview) {
  addFetchTemplatesBtn(listview);
}

function addFetchTemplatesBtn(listview) {
  const DIALOG_TITLE = "Fetching DocuSign Templates";
  const BTN_LABEL = "Fetch DocuSign Templates";

  listview.page.add_inner_button(BTN_LABEL, function () {
    frappe.call({
      method:
        "crm_docusign_integration.docusign.doctype.document_template.document_template.fetch_templates",
      callback: function (response) {
        if (response && response.message) {
          if (response.message.status === "success") {
            frappe.show_alert(
              response.message.msg || "Started fetching DocuSign Templates",
              5,
            );

            function handleRealtimeProgress(msg) {
              progressDialog = frappe.show_progress(
                msg.title || DIALOG_TITLE,
                msg.progress,
                msg.total,
                "Please Wait...",
                true,
              );

              if (msg.progress === msg.total) {
                frappe.show_alert(
                  {
                    indicator: "green",
                    message: "DocuSign templates fetched successfully.",
                  },
                  5,
                );
                frappe.realtime.off(
                  response.message.track_on,
                  handleRealtimeProgress,
                );
              }
            }
            frappe.realtime.on(
              response.message.track_on,
              handleRealtimeProgress,
            );
          } else {
            frappe.throw(
              `Error occured during fetching templates: ${response.message}`,
            );
          }
        }
      },
    });
  });
}
