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

function addGridRect(c0, c1, strokeCells) {
  const minX = Math.min(c0[0], c1[0]);
  const maxX = Math.max(c0[0], c1[0]);
  const minY = Math.min(c0[1], c1[1]);
  const maxY = Math.max(c0[1], c1[1]);
  for (let y = minY; y <= maxY; y += 1) {
    for (let x = minX; x <= maxX; x += 1) {
      strokeCells.set(x + "," + y, [x, y]);
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
  const {
    src,
    grid_w,
    grid_h,
    width,
    height,
    cursor,
    enable_paint,
    pick_on_click,
    paint_mode,
    max_height,
  } = event.detail.args;
  const img = document.getElementById("image");
  const preview = document.getElementById("preview-layer");
  const gridW = parseInt(grid_w, 10);
  const gridH = parseInt(grid_h, 10);
  /* Default enable_paint true when arg omitted (older component cache). */
  const enablePaint = !explicitFalse(enable_paint);
  const pickOnClick = truthy(pick_on_click);
  const paintMode = paint_mode || "cell";
  const maxHeight = Number(max_height || 760);
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
    preview.width = img.width;
    preview.height = img.height;
    preview.style.width = img.width + "px";
    preview.style.height = img.height + "px";
    if (container) {
      container.style.maxHeight = maxHeight + "px";
      container.style.height = Math.min(img.height, maxHeight) + "px";
    }
    const frameHeight = Math.min(img.height + 8, maxHeight + 8);
    Streamlit.setFrameHeight(frameHeight);
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

  function clearPreview() {
    const ctx = preview.getContext("2d");
    ctx.clearRect(0, 0, preview.width, preview.height);
  }

  function drawPreview(cells) {
    const ctx = preview.getContext("2d");
    ctx.clearRect(0, 0, preview.width, preview.height);
    if (!cells || cells.length === 0) {
      return;
    }
    const cellW = img.width / gridW;
    const cellH = img.height / gridH;
    ctx.fillStyle = "rgba(30, 58, 138, 0.28)";
    ctx.strokeStyle = "rgba(30, 58, 138, 0.82)";
    ctx.lineWidth = 1;
    for (const [cx, cy] of cells) {
      const x = cx * cellW;
      const y = cy * cellH;
      ctx.fillRect(x, y, cellW, cellH);
      ctx.strokeRect(x + 0.5, y + 0.5, Math.max(1, cellW - 1), Math.max(1, cellH - 1));
    }
  }

  let painting = false;
  let panning = false;
  let spacePressed = false;
  let panStartX = 0;
  let panStartY = 0;
  let panStartScrollLeft = 0;
  let panStartScrollTop = 0;
  let strokeCells = new Map();
  let startGrid = null;
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
    startGrid = null;
    lastGrid = null;
    painting = false;
    clearPreview();
  }

  function finishPan() {
    if (!panning) {
      return;
    }
    panning = false;
    document.body.classList.remove("is-panning");
    document.documentElement.style.cursor = cur;
    document.body.style.cursor = cur;
    if (container) {
      container.style.cursor = cur;
    }
    img.style.cursor = cur;
  }

  function onWindowMouseUp(ev) {
    if (panning) {
      finishPan();
      return;
    }
    if (!painting) {
      return;
    }
    const rect = img.getBoundingClientRect();
    const ox = ev.clientX - rect.left;
    const oy = ev.clientY - rect.top;
    const g = pixelToGrid(ox, oy, img, gridW, gridH);
    if (g) {
      if (paintMode === "line" && startGrid) {
        strokeCells = new Map();
        addGridLine(startGrid, g, strokeCells);
      } else if (paintMode === "area" && startGrid) {
        strokeCells = new Map();
        addGridRect(startGrid, g, strokeCells);
      } else {
        lastGrid = addCellFromOffsets(ox, oy, img, gridW, gridH, strokeCells, lastGrid);
      }
    }
    finishStroke();
  }

  img.onmousemove = (e) => {
    updateCoord(e.offsetX, e.offsetY);
    if (enablePaint && painting) {
      const g = pixelToGrid(e.offsetX, e.offsetY, img, gridW, gridH);
      if (!g) {
        return;
      }
      if (paintMode === "line" && startGrid) {
        strokeCells = new Map();
        addGridLine(startGrid, g, strokeCells);
        drawPreview(Array.from(strokeCells.values()));
      } else if (paintMode === "area" && startGrid) {
        strokeCells = new Map();
        addGridRect(startGrid, g, strokeCells);
        drawPreview(Array.from(strokeCells.values()));
      } else {
        lastGrid = addCellFromOffsets(e.offsetX, e.offsetY, img, gridW, gridH, strokeCells, lastGrid);
        drawPreview(Array.from(strokeCells.values()));
      }
    }
  };

  img.onclick = null;
  img.onmousedown = null;

  window.onkeydown = (ev) => {
    if (ev.code === "Space") {
      spacePressed = true;
      if (!painting && !panning) {
        document.body.classList.add("is-panning");
        if (container) {
          container.style.cursor = "grab";
        }
        img.style.cursor = "grab";
      }
      ev.preventDefault();
    }
  };
  window.onkeyup = (ev) => {
    if (ev.code === "Space") {
      spacePressed = false;
      if (!panning && !painting) {
        document.body.classList.remove("is-panning");
        if (container) {
          container.style.cursor = cur;
        }
        img.style.cursor = cur;
      }
      ev.preventDefault();
    }
  };

  window.onmousemove = (ev) => {
    if (!panning || !container) {
      return;
    }
    const dx = ev.clientX - panStartX;
    const dy = ev.clientY - panStartY;
    container.scrollLeft = panStartScrollLeft - dx;
    container.scrollTop = panStartScrollTop - dy;
  };

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
    clearPreview();
    return;
  }

  img.onmousedown = (e) => {
    e.preventDefault();
    if (spacePressed && container) {
      panning = true;
      painting = false;
      document.body.classList.add("is-panning");
      panStartX = e.clientX;
      panStartY = e.clientY;
      panStartScrollLeft = container.scrollLeft;
      panStartScrollTop = container.scrollTop;
      window.addEventListener("mouseup", onWindowMouseUp, { once: true });
      return;
    }
    painting = true;
    document.body.classList.add("is-painting");
    document.documentElement.style.cursor = "grabbing";
    document.body.style.cursor = "grabbing";
    if (container) {
      container.style.cursor = "grabbing";
    }
    img.style.cursor = "grabbing";
    strokeCells = new Map();
    startGrid = null;
    lastGrid = null;
    const g = pixelToGrid(e.offsetX, e.offsetY, img, gridW, gridH);
    if (!g) {
      painting = false;
      return;
    }
    startGrid = g;
    if (paintMode === "line" || paintMode === "area") {
      strokeCells.set(g[0] + "," + g[1], g);
    } else {
      lastGrid = addCellFromOffsets(e.offsetX, e.offsetY, img, gridW, gridH, strokeCells, lastGrid);
    }
    drawPreview(Array.from(strokeCells.values()));
    window.addEventListener("mouseup", onWindowMouseUp, { once: true });
  };

  img.onmouseleave = () => {
    /* keep painting until global mouseup */
  };
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
