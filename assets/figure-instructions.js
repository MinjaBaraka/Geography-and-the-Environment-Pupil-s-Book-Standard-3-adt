(function () {
  "use strict";

  var instructions = {
    pg011_n0003: {
      anchorId: "pg011_im003",
      visible: "Listen to the audio description or examine Figure 4 and then answer the questions that follow:",
      audio: "Listen to the audio description or examine Figure 4 and then answer the questions that follow:"
    },
    pg012_n0005: {
      anchorId: "pg012_im001",
      visible: "Listen to the audio description or examine Figure 5 and answer the questions that follow:",
      audio: "Listen to the audio description or examine Figure 5 and answer the questions that follow:"
    },
    pg014_n0010: {
      anchorId: "pg014_im001",
      visible: "Listen to the audio description or examine Figure 6 and answer the questions that follow:",
      audio: "Listen to the audio description or examine Figure 6 and answer the questions that follow:"
    },
    pg022_n0003: {
      anchorId: "pg022_im001",
      visible: "1. Listen to the audio description or examine Figure 1 and identify the relief features:",
      audio: "1. Listen to the audio description or examine Figure 1 and identify the relief features:"
    },
    pg041_n0003: {
      anchorId: "pg041_im001",
      visible: "Listen to the audio description or examine Figure 2, and then identify:",
      audio: "Listen to the audio description or examine Figure 2, and then identify:"
    },
    pg043_n0005: {
      anchorId: "pg043_im003",
      visible: "Listen to the audio description or examine Figure 3; and then identify:",
      audio: "Listen to the audio description or examine Figure 3; and then identify:"
    },
    pg079_n0012: {
      anchorId: "pg079_im001",
      visible: "Listen to the audio description or examine Figure 13 and then answer the questions that follow.",
      audio: "Listen to the audio description or examine Figure 13 and then answer the questions that follow."
    }
  };

  function makeAudioText(id, text) {
    var span = document.createElement("span");
    span.className = "sr-only";
    span.setAttribute("data-id", id);
    span.setAttribute("data-figure-instruction-audio", id);
    span.textContent = text;
    return span;
  }

  function installInstruction(id, instruction) {
    if (document.querySelector('[data-figure-instruction-audio="' + id + '"]')) return;

    var visibleText = document.querySelector('[data-id="' + id + '"]');
    var audioText = makeAudioText(id, instruction.audio);

    if (visibleText) {
      visibleText.removeAttribute("data-id");
      visibleText.setAttribute("aria-hidden", "true");
      visibleText.textContent = instruction.visible;
    } else {
      var visibleCandidates = Array.prototype.slice.call(
        document.querySelectorAll("p, div, span")
      ).filter(function (element) {
        return element.textContent.trim().indexOf(instruction.visible) === 0;
      }).sort(function (left, right) {
        return left.textContent.length - right.textContent.length;
      });
      if (visibleCandidates.length) {
        visibleCandidates[0].setAttribute("aria-hidden", "true");
      }
    }

    var anchor = instruction.anchorId
      ? document.querySelector('[data-id="' + instruction.anchorId + '"]')
      : null;
    if (anchor) {
      anchor.insertAdjacentElement("beforebegin", audioText);
    } else if (visibleText) {
      visibleText.insertAdjacentElement("afterend", audioText);
    }
  }

  function installAll() {
    Object.keys(instructions).forEach(function (id) {
      installInstruction(id, instructions[id]);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      installAll();
      window.setTimeout(installAll, 250);
    });
  } else {
    installAll();
    window.setTimeout(installAll, 250);
  }
  window.addEventListener("load", installAll);
})();
