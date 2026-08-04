(function () {
  "use strict";

  var BOOK_STORAGE_PREFIX = "adt-geography-standard-3:";

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

    var instruction = element("p", {
      class: "inclusive-instruction",
      id: meta.instructionId,
      "data-id": meta.instructionId,
    }, meta.instruction);
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
    var textareas = Array.from(
      document.querySelectorAll(
        'section[data-section-type="activity_open_ended_answer"] textarea:not([data-no-drawing])'
      )
    );
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

