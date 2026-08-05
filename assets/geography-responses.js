(function () {
  "use strict";

  // Drawing and Braille response conversion is only used for eligible
  // Kuandika/Writing titles below Standard 3. This Geography title keeps
  // its native lined writing areas.
  var DRAWING_RESPONSES_ENABLED = false;
  var BOOK_STORAGE_PREFIX = "adt-geography-standard-3:";
  var EXPLICIT_ACTIVITY_PROMPTS = {
    "pg022_sec001:1": ["pg022_n0003"],
    "pg024_sec001:1": ["pg024_n0003", "pg024_n0004"],
    "pg044_sec001:1": ["pg044_n0005", "pg044_n0006", "pg044_n0007"],
  };

  function storageKey(id) {
    return BOOK_STORAGE_PREFIX + location.pathname + ":" + id;
  }

  function readStored(id) {
    try {
      return window.localStorage.getItem(storageKey(id));
    } catch (_error) {
      return null;
    }
  }

  function writeStored(id, value) {
    try {
      window.localStorage.setItem(storageKey(id), value);
    } catch (_error) {
      // Drawing remains available when storage is unavailable or full.
    }
  }

  function removeStored(id) {
    try {
      window.localStorage.removeItem(storageKey(id));
    } catch (_error) {
      // Clearing the visible response still works without local storage.
    }
  }

  function dispatchResponseEvent(control) {
    control.dispatchEvent(new Event("input", { bubbles: true }));
    control.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function slug(value) {
    return String(value || "response")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function responseMetadata(textarea, index) {
    var section = textarea.closest("section[data-section-id]");
    var sectionId = section ? section.getAttribute("data-section-id") : "page";
    var baseId = sectionId + "-drawing-" + String(index + 1).padStart(2, "0");
    var answerLabel = textarea.getAttribute("aria-label") || "this question";
    var taskType = textarea.getAttribute("data-accessible-task-type") || "handwritten-text-response";
    var expectedType = textarea.getAttribute("data-expected-response-type") || "text";
    var tactileRequired = textarea.getAttribute("data-tactile-resource-required") === "true";
    var customInstruction = textarea.getAttribute("data-inclusive-instruction");
    var instruction = customInstruction ||
      "Handwrite or draw your answer in the response space, or enter it using a keyboard or Braille.";

    return {
      answerLabel: answerLabel,
      baseId: baseId,
      expectedType: expectedType,
      instruction: instruction,
      instructionId: baseId + "-inclusive-instruction",
      proxyAriaId: textarea.getAttribute("data-aria-id") || slug(baseId + "-response"),
      tactileRequired: tactileRequired,
      taskType: taskType,
    };
  }

  function hasResponseControl(node) {
    return Boolean(
      node &&
      node.querySelector &&
      node.querySelector("textarea, input, canvas, select, button, table, figure, img")
    );
  }

  function isPromptCandidate(node) {
    if (!node || hasResponseControl(node)) return false;
    if (node.matches("h1, h2, h3, h4, h5, h6")) return false;
    return node.textContent.replace(/\s+/g, " ").trim().length > 0;
  }

  function explicitPromptElements(textarea, section, responseIndex) {
    if (!section) return [];
    var responseNumber = responseIndex + 1;
    var key = section.getAttribute("data-section-id") + ":" + responseNumber;
    var ids = EXPLICIT_ACTIVITY_PROMPTS[key];
    if (!ids) return [];

    var nodes = ids.map(function (id) {
      return section.querySelector('[data-id="' + id + '"]');
    }).filter(Boolean);
    if (!nodes.length) return [];
    if (nodes.length === 1) {
      return [nodes[0].closest("p, label, div") || nodes[0]];
    }

    var common = nodes[0].parentElement;
    while (
      common &&
      common !== section &&
      !nodes.every(function (node) { return common.contains(node); })
    ) {
      common = common.parentElement;
    }
    return common && common !== section ? [common] : nodes;
  }

  function associatedPromptElements(textarea, responseIndex) {
    var section = textarea.closest("section[data-section-id]");
    var explicitPrompts = explicitPromptElements(textarea, section, responseIndex);
    if (explicitPrompts.length) return explicitPrompts;
    var promptSelector = textarea.getAttribute("data-inclusive-prompt-selector");
    if (promptSelector) {
      var selectedPrompt = document.querySelector(promptSelector);
      if (isPromptCandidate(selectedPrompt)) return [selectedPrompt];
    }
    var previous = textarea.previousElementSibling;

    if (isPromptCandidate(previous)) {
      if (previous.matches("p, label, span")) {
        var prompts = [];
        while (
          previous &&
          previous.matches("p, label, span") &&
          isPromptCandidate(previous)
        ) {
          prompts.unshift(previous);
          previous = previous.previousElementSibling;
        }
        return prompts;
      }
      return [previous];
    }

    var current = textarea.parentElement;
    while (current && current !== section) {
      previous = current.previousElementSibling;
      if (isPromptCandidate(previous)) return [previous];
      current = current.parentElement;
    }
    return [];
  }

  function appendPromptContent(source, target) {
    function appendNode(node, destination) {
      if (node.nodeType === Node.TEXT_NODE) {
        destination.appendChild(document.createTextNode(node.textContent));
        return;
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return;
      if (node.tagName === "BR") {
        destination.appendChild(document.createTextNode(" "));
        return;
      }

      var nextDestination = destination;
      if (node.hasAttribute("data-id")) {
        var span = document.createElement("span");
        ["data-id", "aria-label", "lang", "data-tts-ignore", "aria-hidden"].forEach(
          function (attribute) {
            if (node.hasAttribute(attribute)) {
              span.setAttribute(attribute, node.getAttribute(attribute));
            }
          }
        );
        destination.appendChild(span);
        nextDestination = span;
      }
      Array.from(node.childNodes).forEach(function (child) {
        appendNode(child, nextDestination);
      });
    }

    appendNode(source, target);
  }

  function buildInclusiveInstruction(textarea, meta, responseIndex) {
    var instruction = element("p", {
      class: "inclusive-instruction",
      id: meta.instructionId,
    });
    var prompts = associatedPromptElements(textarea, responseIndex);

    if (prompts.length) {
      prompts.forEach(function (prompt, promptIndex) {
        if (promptIndex) instruction.appendChild(document.createTextNode(" "));
        appendPromptContent(prompt, instruction);
      });
      prompts.forEach(function (prompt) {
        prompt.remove();
      });
    } else {
      instruction.appendChild(document.createTextNode(meta.answerLabel));
    }

    instruction.appendChild(document.createTextNode(" "));
    instruction.appendChild(element("span", {
      "data-id": meta.instructionId,
    }, meta.instruction));
    return instruction;
  }

  function mergeSharedQuestionTextareas(textareas) {
    return textareas.filter(function (textarea, index) {
      if (!index) return true;
      var previous = textareas[index - 1];
      if (
        textarea.parentElement !== previous.parentElement ||
        textarea.previousElementSibling !== previous
      ) {
        return true;
      }

      var previousLabel = previous.getAttribute("aria-label") || "Answer";
      var currentLabel = textarea.getAttribute("aria-label") || "additional answer";
      previous.setAttribute("aria-label", previousLabel + "; " + currentLabel);
      textarea.remove();
      return false;
    });
  }

  function element(name, attributes, text) {
    var node = document.createElement(name);
    Object.keys(attributes || {}).forEach(function (key) {
      if (attributes[key] !== null && attributes[key] !== undefined) {
        node.setAttribute(key, String(attributes[key]));
      }
    });
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function buildDrawingResponse(textarea, index) {
    var meta = responseMetadata(textarea, index);
    var wrapper = element("div", {
      class: "accessible-drawing-response",
      "data-drawing-response-id": meta.baseId,
    });

    var instruction = buildInclusiveInstruction(textarea, meta, index);
    wrapper.appendChild(instruction);

    var canvasWrap = element("div", {
      class: "geography-canvas-wrap",
      role: "group",
      "aria-labelledby": meta.instructionId,
    });
    var canvas = element("canvas", {
      class: "geography-drawing-canvas",
      id: meta.baseId,
      role: "img",
      tabindex: "0",
      "aria-label": "Blank drawing area for " + meta.answerLabel + ". Use touch, pen, or mouse to handwrite or draw the answer.",
      "aria-describedby": meta.instructionId,
      "data-practice-storage": meta.baseId,
    });
    canvasWrap.appendChild(canvas);
    wrapper.appendChild(canvasWrap);

    var toolbar = element("div", {
      class: "drawing-toolbar",
      role: "group",
      "aria-label": "Drawing controls for " + meta.answerLabel,
    });
    toolbar.appendChild(element("button", {
      type: "button",
      "data-undo-canvas": meta.baseId,
      "aria-label": "Undo the last stroke for " + meta.answerLabel,
    }, "Undo last stroke"));
    toolbar.appendChild(element("button", {
      type: "button",
      "data-clear-canvas": meta.baseId,
      "aria-label": "Clear the drawing for " + meta.answerLabel,
    }, "Clear drawing"));
    wrapper.appendChild(toolbar);

    var statusRow = element("div", { class: "drawing-status-row" });
    var statusLabelId = meta.baseId + "-response-label";
    statusRow.appendChild(element("label", {
      for: meta.baseId + "-response",
      id: statusLabelId,
    }, "Response status"));
    statusRow.appendChild(element("input", {
      class: "drawing-response",
      id: meta.baseId + "-response",
      type: "text",
      readonly: "readonly",
      placeholder: "Draw, type, or use Braille",
      "aria-labelledby": statusLabelId,
      "aria-describedby": meta.instructionId,
      "data-canvas-response": meta.baseId,
      "data-practice-storage": meta.baseId + "-response",
      "data-aria-id": meta.proxyAriaId,
    }));
    wrapper.appendChild(statusRow);

    var alternative = element("div", {
      class: "integrated-text-response",
      role: "group",
      "aria-labelledby": meta.baseId + "-alternative-label",
      "data-accessible-task-type": meta.taskType,
      "data-expected-response-type": meta.expectedType,
      "data-inclusive-instruction": meta.instruction,
      "data-braille-code": "pending-specialist-review",
      "data-tactile-resource-required": String(meta.tactileRequired),
    });
    alternative.appendChild(element("label", {
      for: meta.baseId + "-alternative",
      id: meta.baseId + "-alternative-label",
    }, "Keyboard or Braille answer (optional when a drawing is saved)"));
    alternative.appendChild(element("input", {
      class: "drawing-alternative-input",
      id: meta.baseId + "-alternative",
      type: "search",
      role: "textbox",
      inputmode: "text",
      autocomplete: "off",
      "aria-labelledby": meta.baseId + "-alternative-label",
      "aria-describedby": meta.instructionId,
      "data-canvas-alternative": meta.baseId,
      "data-practice-storage": meta.baseId + "-alternative",
    }));
    alternative.appendChild(element("p", {
      class: "drawing-help",
      id: meta.baseId + "-alternative-help",
    }, "This native field works with ordinary keyboards, screen readers, refreshable Braille displays, Braille keyboards, and operating-system Braille input."));
    wrapper.appendChild(alternative);

    textarea.replaceWith(wrapper);
    return canvas;
  }

  function initialiseTextControl(control) {
    var id = control.getAttribute("data-practice-storage");
    if (!id) return;
    var stored = readStored(id);
    if (stored !== null) control.value = stored;
    control.addEventListener("input", function () {
      writeStored(id, control.value);
    });
  }

  function alternativeValue(canvas) {
    var alternative = document.querySelector(
      '[data-canvas-alternative="' + canvas.id + '"]'
    );
    return alternative ? alternative.value.trim() : "";
  }

  function updateCanvasResponse(canvas, hasDrawing) {
    var response = document.querySelector(
      '[data-canvas-response="' + canvas.id + '"]'
    );
    if (!response) return;
    var complete = hasDrawing || alternativeValue(canvas) !== "";
    var nextValue = complete ? "Response completed" : "";
    if (response.value !== nextValue) {
      response.value = nextValue;
      writeStored(response.getAttribute("data-practice-storage"), nextValue);
      dispatchResponseEvent(response);
    }
    response.classList.toggle("is-complete", complete);
  }

  function parseStrokes(value) {
    if (!value) return [];
    try {
      var parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
      return [];
    }
  }

  function initialiseCanvas(canvas) {
    var context = canvas.getContext("2d");
    var id = canvas.getAttribute("data-practice-storage") || canvas.id;
    var strokes = parseStrokes(readStored(id));
    var activeStroke = null;
    var drawing = false;
    var pixelRatio = Math.max(1, window.devicePixelRatio || 1);

    function resizeCanvas() {
      var rect = canvas.getBoundingClientRect();
      var width = Math.max(1, Math.round(rect.width * pixelRatio));
      var height = Math.max(1, Math.round(rect.height * pixelRatio));
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      render();
    }

    function drawStroke(stroke) {
      if (!stroke || stroke.length < 2) return;
      context.beginPath();
      context.moveTo(stroke[0].x * canvas.width, stroke[0].y * canvas.height);
      for (var i = 1; i < stroke.length; i += 1) {
        context.lineTo(stroke[i].x * canvas.width, stroke[i].y * canvas.height);
      }
      context.stroke();
    }

    function render() {
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.lineCap = "round";
      context.lineJoin = "round";
      context.lineWidth = Math.max(4 * pixelRatio, canvas.width * 0.004);
      context.strokeStyle = "#172033";
      strokes.forEach(drawStroke);
      if (activeStroke) drawStroke(activeStroke);
    }

    function pointFromEvent(event) {
      var rect = canvas.getBoundingClientRect();
      return {
        x: Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)),
        y: Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)),
      };
    }

    function save() {
      if (strokes.length) writeStored(id, JSON.stringify(strokes));
      else removeStored(id);
      canvas.dataset.hasDrawing = strokes.length ? "true" : "false";
      updateCanvasResponse(canvas, strokes.length > 0);
    }

    canvas.addEventListener("pointerdown", function (event) {
      event.preventDefault();
      drawing = true;
      activeStroke = [pointFromEvent(event)];
      canvas.setPointerCapture(event.pointerId);
    });

    canvas.addEventListener("pointermove", function (event) {
      if (!drawing || !activeStroke) return;
      event.preventDefault();
      activeStroke.push(pointFromEvent(event));
      render();
    });

    function finishDrawing(event) {
      if (!drawing) return;
      drawing = false;
      if (event && canvas.hasPointerCapture(event.pointerId)) {
        canvas.releasePointerCapture(event.pointerId);
      }
      if (activeStroke && activeStroke.length > 1) strokes.push(activeStroke);
      activeStroke = null;
      render();
      save();
    }

    canvas.addEventListener("pointerup", finishDrawing);
    canvas.addEventListener("pointercancel", finishDrawing);

    var undoButton = document.querySelector('[data-undo-canvas="' + canvas.id + '"]');
    if (undoButton) {
      undoButton.addEventListener("click", function () {
        strokes.pop();
        render();
        save();
        canvas.focus();
      });
    }

    var clearButton = document.querySelector('[data-clear-canvas="' + canvas.id + '"]');
    if (clearButton) {
      clearButton.addEventListener("click", function () {
        strokes = [];
        activeStroke = null;
        render();
        save();
        canvas.focus();
      });
    }

    var alternative = document.querySelector(
      '[data-canvas-alternative="' + canvas.id + '"]'
    );
    if (alternative) {
      alternative.addEventListener("input", function () {
        updateCanvasResponse(canvas, strokes.length > 0);
      });
    }

    canvas.dataset.hasDrawing = strokes.length ? "true" : "false";
    if (window.ResizeObserver) {
      new ResizeObserver(resizeCanvas).observe(canvas);
    } else {
      window.addEventListener("resize", resizeCanvas);
    }
    resizeCanvas();
    updateCanvasResponse(canvas, strokes.length > 0);
  }

  function initialise() {
    if (!DRAWING_RESPONSES_ENABLED) return;
    var textareas = Array.from(
      document.querySelectorAll(
        'section[data-section-type="activity_open_ended_answer"] textarea:not([data-no-drawing])'
      )
    );
    textareas = mergeSharedQuestionTextareas(textareas);
    var canvases = textareas.map(buildDrawingResponse);
    document
      .querySelectorAll('input[data-practice-storage]:not([data-canvas-response])')
      .forEach(initialiseTextControl);
    canvases.forEach(initialiseCanvas);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialise, { once: true });
  } else {
    initialise();
  }
})();
