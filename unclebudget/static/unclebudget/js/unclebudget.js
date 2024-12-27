"use strict";

function envelopeChange(select) {
  let foundBlankSelect = false;
  for (const envelopeSelect of document.getElementsByName("item_envelope")) {
    if (envelopeSelect.value !== "") {
      continue;
    }

    if (foundBlankSelect) {
      console.log("removing");
      console.log(envelopeSelect.parentElement.parentElement);
      envelopeSelect.parentElement.parentElement.remove();
    }

    foundBlankSelect = true;
  }

  if (!foundBlankSelect) {
    const tr = select.parentElement.parentElement;
    const newRow = tr.cloneNode(true);

    newRow.querySelectorAll("input").forEach((input) => (input.value = ""));

    tr.after(newRow);
  }
}

function stickyQuickAdvance() {
  const quickAdvance = document.getElementsByName("quick-advance")[0];
  if (!quickAdvance) {
    return;
  }

  const value = localStorage.getItem("quick-advance");
  quickAdvance.checked = value;
}
window.addEventListener("load", stickyQuickAdvance);

function quickAdvanceChange(element) {
  if (element.checked) {
    localStorage.setItem("quick-advance", "y");
  } else {
    localStorage.setItem("quick-advance", "");
  }
}
