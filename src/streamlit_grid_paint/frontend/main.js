function pixelToGrid(offsetX, offsetY, img, gridW, gridH) {
  if (offsetX < 0 || offsetY < 0 || offsetX >= img.width || offsetY >= img.height) {
    return null;
  }
  const cx = Math.max(0, Math.min(gridW - 1, Math.floor((offsetX * gridW) / img.width)));
  const cy = Math.max(0, Math.min(gridH - 1, Math.floor((offsetY * gridH) / img.height)));
  return [cx, cy];
}

function addGridLine(c0, c1, strokeCells) {
  let x0 = c0[0];
  let y0 = c0[1];
  const x1 = c1[0];
  const y1 = c1[1];
  const dx = Math.abs(x1 - x0);
  const dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  for (;;) {
    strokeCells.set(x0 + "," + y0, [x0, y0]);
    if (x0 === x1 && y0 === y1) {
      break;
    }
    const e2 = 2 * err;
    if (e2 > -dy) {
      err -= dy;
      x0 += sx;
    }
    if (e2 < dx) {
      err += dx;
      y0 += sy;
    }
  }
}

function addCellFromOffsets(offsetX, offsetY, img, gridW, gridH, strokeCells, lastGrid) {
  const g = pixelToGrid(offsetX, offsetY, img, gridW, gridH);
  if (!g) {
    return lastGrid;
  }
  if (lastGrid) {
    addGridLine(lastGrid, g, strokeCells);
  } else {
    strokeCells.set(g[0] + "," + g[1], g);
  }
  return g;
}

function truthy(v) {
  return v === true || v === 1 || v === "1" || v === "true";
}

function explicitFalse(v) {
  return v === false || v === 0 || v === "false" || v === "0";
}

function onRender(event) {
  const { src, grid_w, grid_h, width, height, cursor, enable_paint, pick_on_click } = event.detail.args;
  const img = document.getElementById("image");
  const gridW = parseInt(grid_w, 10);
  const gridH = parseInt(grid_h, 10);
  /* Default enable_paint true when arg omitted (older component cache). */
  const enablePaint = !explicitFalse(enable_paint);
  const pickOnClick = truthy(pick_on_click);
  const coordEl = document.getElementById("coord-hint");

  if (img.src !== src) {
    img.src = src;
  }

  const cur = cursor || "crosshair";
  document.documentElement.style.cursor = cur;
  document.body.style.cursor = cur;
  const container = document.getElementById("image-container");
  if (container) {
    container.style.cursor = cur;
  }
  img.style.cursor = cur;

  function resizeImage() {
    img.removeAttribute("width");
    img.removeAttribute("height");
    if (width && height) {
      img.width = width;
      img.height = height;
    } else if (width) {
      img.width = width;
      img.height = Math.max(1, Math.round((width * img.naturalHeight) / img.naturalWidth));
    } else if (height) {
      img.height = height;
      img.width = Math.max(1, Math.round((height * img.naturalWidth) / img.naturalHeight));
    } else {
      img.width = img.naturalWidth;
      img.height = img.naturalHeight;
    }
    Streamlit.setFrameHeight(img.height + 8);
  }

  img.onload = resizeImage;
  if (img.complete && img.naturalWidth) {
    resizeImage();
  }

  function updateCoord(ox, oy) {
    if (!coordEl) {
      return;
    }
    const g = pixelToGrid(ox, oy, img, gridW, gridH);
    coordEl.textContent = g ? `col ${g[0]} · fila ${g[1]}` : "col — · fila —";
  }

  let painting = false;
  let strokeCells = new Map();
  let lastGrid = null;

  function finishStroke() {
    document.body.classList.remove("is-painting");
    document.documentElement.style.cursor = cur;
    document.body.style.cursor = cur;
    if (container) {
      container.style.cursor = cur;
    }
    img.style.cursor = cur;
    if (strokeCells.size > 0) {
      Streamlit.setComponentValue({
        kind: "stroke",
        stroke_id: Date.now(),
        cells: Array.from(strokeCells.values()),
        width: img.width,
        height: img.height,
      });
    }
    strokeCells = new Map();
    lastGrid = null;
    painting = false;
  }

  function onWindowMouseUp(ev) {
    if (!painting) {
      return;
    }
    const rect = img.getBoundingClientRect();
    const ox = ev.clientX - rect.left;
    const oy = ev.clientY - rect.top;
    lastGrid = addCellFromOffsets(ox, oy, img, gridW, gridH, strokeCells, lastGrid);
    finishStroke();
  }

  img.onmousemove = (e) => {
    updateCoord(e.offsetX, e.offsetY);
    if (enablePaint && painting) {
      lastGrid = addCellFromOffsets(e.offsetX, e.offsetY, img, gridW, gridH, strokeCells, lastGrid);
    }
  };

  img.onclick = null;
  img.onmousedown = null;

  if (!enablePaint && pickOnClick) {
    img.onclick = (e) => {
      e.preventDefault();
      const g = pixelToGrid(e.offsetX, e.offsetY, img, gridW, gridH);
      if (g) {
        Streamlit.setComponentValue({
          kind: "pick",
          cx: g[0],
          cy: g[1],
          pick_id: Date.now(),
          width: img.width,
          height: img.height,
        });
      }
    };
    return;
  }

  if (!enablePaint) {
    return;
  }

  img.onmousedown = (e) => {
    e.preventDefault();
    painting = true;
    document.body.classList.add("is-painting");
    document.documentElement.style.cursor = "grabbing";
    document.body.style.cursor = "grabbing";
    if (container) {
      container.style.cursor = "grabbing";
    }
    img.style.cursor = "grabbing";
    strokeCells = new Map();
    lastGrid = null;
    lastGrid = addCellFromOffsets(e.offsetX, e.offsetY, img, gridW, gridH, strokeCells, lastGrid);
    window.addEventListener("mouseup", onWindowMouseUp, { once: true });
  };

  img.onmouseleave = () => {
    /* keep painting until global mouseup */
  };
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
