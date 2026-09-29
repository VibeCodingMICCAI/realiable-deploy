(() => {
  const screens = ["explore", "tests"];
  const state = {
    live: null,
    introMeta: null,
    slicePos: 0,
    viewMode: "overlay",
    opacity: 55,
    busy: false
  };

  const EXPECTED_FAILURE_IDS = new Set([
    "mean_dice_reveal",
    "mean_dice_regression_faulty",
    "overlay_reveal",
    "overlay_regression_faulty",
    "stale_regression_faulty",
    "stale_sequential_faulty"
  ]);

  function show(id) {
    if (!screens.includes(id)) id = "explore";
    screens.forEach((name) => {
      const el = document.getElementById(name);
      if (el) el.classList.toggle("hidden", name !== id);
    });
    document.querySelectorAll(".nav-tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.go === id);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (id === "explore") renderIntro();
  }

  document.body.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-go]");
    if (!btn) return;
    if (btn.tagName === "A") return;
    event.preventDefault();
    show(btn.dataset.go);
  });

  const labBanner = document.getElementById("lab-banner");
  async function probeLab() {
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      const data = await res.json();
      state.live = !!data.ok;
    } catch (err) {
      state.live = false;
    }
    if (!labBanner) return;
    if (state.live) {
      labBanner.className = "lab-banner live";
      labBanner.textContent =
        "Live lab: allowlisted Python on this machine. Cached demo still uses the packaged prediction (not fresh nnU-Net inference).";
    } else {
      labBanner.className = "lab-banner sample";
      labBanner.textContent =
        "Sample mode: pre-recorded results. For live checks run python scripts/tutorial_lab.py then Ctrl+F5.";
    }
  }

  function formatResult(data) {
    const lines = [];
    if (data.mode === "sample") lines.push("[PRE-RECORDED SAMPLE — not executed in the browser]");
    if (data.expected_failure) lines.push("[EXPECTED FAILURE — seeded defect detected]");
    if (data.ok === false && !data.expected_failure && data.error)
      lines.push("[UNEXPECTED ERROR]");
    lines.push("$ " + (data.command || data.action || data.challenge_id || ""));
    lines.push("mode: " + (data.mode || "?"));
    if (data.message) lines.push(data.message);
    if (data.error) lines.push("ERROR: " + data.error);
    (data.checks || []).forEach((c) => {
      lines.push((c.pass ? "PASS" : "FAIL") + "  " + c.name);
      if (c.expected !== undefined) lines.push("  expected: " + JSON.stringify(c.expected));
      if (c.observed !== undefined) lines.push("  observed: " + JSON.stringify(c.observed));
      if (c.detail) lines.push("  detail: " + c.detail);
    });
    const meta = data.meta || {};
    if (meta.gate || meta.teaching_prediction || meta.strong) {
      const gate = meta.gate || meta.teaching_prediction || meta.strong;
      if (gate && gate.per_label) {
        lines.push("");
        lines.push("--- Per-label Dice ---");
        Object.keys(gate.per_label).forEach((k) => {
          lines.push("  label " + k + ": " + gate.per_label[k]);
        });
        if (gate.mean_dice !== undefined) lines.push("  mean: " + gate.mean_dice);
      }
    }
    if (meta.result && meta.result.overlay_z !== undefined) {
      lines.push("");
      lines.push("--- Overlay binding ---");
      lines.push("policy: " + meta.result.policy);
      lines.push("overlay_z: " + meta.result.overlay_z + "  expected_z: " + meta.result.expected_z);
      lines.push("matches_expected: " + meta.result.overlay_matches_expected);
    }
    if (data.explanation) lines.push("\n" + data.explanation);
    return lines.join("\n");
  }

  function setBusy(on) {
    state.busy = on;
    document.querySelectorAll("#tests .run-btn").forEach((b) => {
      if (on) {
        if (!b.dataset.prevLabel) b.dataset.prevLabel = b.textContent;
        if (b.dataset.busyLabel) b.textContent = b.dataset.busyLabel;
        b.disabled = true;
      } else {
        if (b.dataset.prevLabel) b.textContent = b.dataset.prevLabel;
        b.disabled = false;
      }
    });
  }

  async function fetchAction(path) {
    let data;
    if (state.live) {
      const res = await fetch("/api/run/" + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}"
      });
      data = await res.json();
    } else if (path.startsWith("challenge/")) {
      const id = path.slice("challenge/".length);
      const res = await fetch("assets/samples/" + id + ".json", { cache: "no-store" });
      data = await res.json();
      data.mode = "sample";
      if (EXPECTED_FAILURE_IDS.has(id) || data.expected_failure) data.expected_failure = true;
    } else {
      data = { ok: false, mode: "sample", error: "Unknown action in sample mode: " + path };
    }
    return data;
  }

  async function runAction(path) {
    if (state.busy) return null;
    setBusy(true);
    try {
      return await fetchAction(path);
    } finally {
      setBusy(false);
    }
  }

  function pad3(n) {
    return String(n).padStart(3, "0");
  }

  function renderIntro() {
    const meta = state.introMeta;
    if (!meta) return;
    const indices = meta.slice_indices;
    const slider = document.getElementById("slice-slider");
    if (!slider) return;
    slider.max = String(indices.length - 1);
    slider.value = String(state.slicePos);
    const z = indices[state.slicePos];
    document.getElementById("slice-label").textContent =
      z + " / axis 2 (exported " + meta.slice_count_exported + " of " + meta.slice_count_total +
      " slices, step " + meta.export_step + ")";
    document.getElementById("intro-slice-caption").textContent =
      "Packaged case " + meta.case_id + " · " + meta.note;

    const mode = state.viewMode;
    const img = document.getElementById("intro-img");
    const overlayLayer = document.getElementById("intro-overlay-img");
    if (mode === "overlay") {
      img.src = "assets/intro_slices/mri_" + pad3(z) + ".png";
      overlayLayer.style.backgroundImage = "url(assets/intro_slices/overlay_" + pad3(z) + ".png)";
      overlayLayer.style.opacity = String(state.opacity / 100);
      overlayLayer.classList.remove("hidden-layer");
    } else {
      const key = mode === "pred" ? "pred_" : "mri_";
      img.src = "assets/intro_slices/" + key + pad3(z) + ".png";
      overlayLayer.classList.add("hidden-layer");
    }

    document.getElementById("intro-legend").innerHTML = Object.keys(meta.labels)
      .map((k) => {
        const hex = meta.label_colors_hex[k];
        return '<span class="legend-item"><i style="background:' + hex + '"></i>' + k + " · " + meta.labels[k] + "</span>";
      })
      .join("");

    document.getElementById("intro-tech").innerHTML =
      "<ul>" +
      "<li>Format: " + meta.file_format + "</li>" +
      "<li>Volume shape: " + meta.volume_shape.join(" × ") + " (3D); display is one 2D " + meta.view_axis + " slice</li>" +
      "<li>Voxel spacing (mm, from affine): " + meta.voxel_spacing_mm.join(" × ") + "</li>" +
      "<li>Model: cached tutorial extract — optional real nnU-Net path documented in <code>model/README.md</code></li>" +
      "<li>Ground-truth label map is packaged for checking tutorials; it is not an inference input.</li>" +
      "<li>Demo outputs:</li></ul><ul>" +
      meta.outputs_described.map((o) => "<li><code>" + o.path + "</code> — " + o.role + "</li>").join("") +
      "</ul>";
  }

  document.getElementById("slice-slider")?.addEventListener("input", (e) => {
    state.slicePos = Number(e.target.value);
    renderIntro();
  });
  document.getElementById("view-mode")?.addEventListener("change", (e) => {
    state.viewMode = e.target.value;
    renderIntro();
  });
  document.getElementById("opacity-slider")?.addEventListener("input", (e) => {
    state.opacity = Number(e.target.value);
    renderIntro();
  });

  function wireReveal(btnId, panelId) {
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    if (!btn || !panel) return;
    btn.addEventListener("click", () => panel.classList.toggle("hidden"));
  }
  wireReveal("reveal-expectations", "expectations");
  wireReveal("reveal-mean-dx", "mean-dx");
  wireReveal("reveal-overlay-dx", "overlay-dx");

  function copyFrom(elId, btn) {
    const el = document.getElementById(elId);
    if (!el) return;
    navigator.clipboard.writeText(el.textContent).then(
      () => {
        const prev = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1200);
      },
      () => {
        btn.textContent = "Copy failed — select manually";
      }
    );
  }

  document.getElementById("copy-mean-prompt")?.addEventListener("click", (e) =>
    copyFrom("mean-prompt", e.currentTarget)
  );
  document.getElementById("copy-overlay-prompt")?.addEventListener("click", (e) =>
    copyFrom("overlay-prompt", e.currentTarget)
  );
  document.getElementById("copy-mean-prompt-footer")?.addEventListener("click", (e) =>
    copyFrom("mean-prompt", e.currentTarget)
  );
  document.getElementById("copy-overlay-prompt-footer")?.addEventListener("click", (e) =>
    copyFrom("overlay-prompt", e.currentTarget)
  );

  async function writeTerm(termId, path, after) {
    const term = document.getElementById(termId);
    if (!term) return;
    term.textContent = "Running…";
    const data = await runAction(path);
    if (!data) {
      term.textContent = "Busy — wait for the current run to finish.";
      return;
    }
    term.textContent = formatResult(data);
    if (after) after(data);
  }

  document.getElementById("run-mean-weak")?.addEventListener("click", () =>
    writeTerm("mean-terminal", "challenge/mean_dice_weak")
  );
  document.getElementById("run-mean-reveal")?.addEventListener("click", () =>
    writeTerm("mean-terminal", "challenge/mean_dice_reveal", (data) => {
      const panel = document.getElementById("mean-compare");
      const text = document.getElementById("mean-compare-text");
      const bad = (data.meta && data.meta.teaching_prediction) || {};
      if (text) {
        text.textContent =
          "Mean Dice ≈ " +
          (bad.mean_dice ?? "?") +
          " while Lateral Tibial Cartilage (label 5) Dice = " +
          (bad.critical_dice ?? 0) +
          ".";
      }
      panel?.classList.remove("hidden");
    })
  );
  document.getElementById("run-mean-faulty")?.addEventListener("click", () =>
    writeTerm("mean-verify", "challenge/mean_dice_regression_faulty")
  );
  document.getElementById("run-mean-fixed")?.addEventListener("click", () =>
    writeTerm("mean-verify", "challenge/mean_dice_regression_corrected")
  );

  document.getElementById("run-overlay-weak")?.addEventListener("click", () =>
    writeTerm("overlay-terminal", "challenge/overlay_weak")
  );
  document.getElementById("run-overlay-reveal")?.addEventListener("click", () =>
    writeTerm("overlay-terminal", "challenge/overlay_reveal", (data) => {
      const panel = document.getElementById("overlay-compare");
      const text = document.getElementById("overlay-compare-text");
      const bad = (data.meta && data.meta.faulty) || {};
      if (text && bad.overlay_z !== undefined) {
        text.textContent =
          "Prediction NIfTI saved correctly; overlay written at z=" +
          bad.overlay_z +
          " instead of mid-slice z=" +
          bad.expected_z +
          ".";
      }
      panel?.classList.remove("hidden");
    })
  );
  document.getElementById("run-overlay-faulty")?.addEventListener("click", () =>
    writeTerm("overlay-verify", "challenge/overlay_regression_faulty")
  );
  document.getElementById("run-overlay-fixed")?.addEventListener("click", () =>
    writeTerm("overlay-verify", "challenge/overlay_regression_corrected")
  );

  fetch("assets/intro_meta.json", { cache: "no-store" })
    .then((r) => r.json())
    .then((meta) => {
      state.introMeta = meta;
      const mid = Math.floor((meta.slice_indices.length - 1) / 2);
      state.slicePos = mid;
      renderIntro();
    })
    .catch(() => {
      document.getElementById("intro-slice-caption").textContent =
        "Could not load intro assets. Run: python scripts/export_intro_slices.py";
    });

  probeLab();
  show("explore");
})();
