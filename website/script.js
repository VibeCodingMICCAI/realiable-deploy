(() => {
  const EVIDENCE_KEY = "vibe_evidence_v3";
  const screens = ["landing", "intro", "core", "challenges", "handover", "summary"];

  const state = {
    live: null,
    route: "quick",
    content: null,
    introMeta: null,
    slicePos: 0,
    viewMode: "overlay",
    opacity: 55,
    coreStep: 1,
    staleSession: null,
    reusePolicy: true,
    revealedReadme: false,
    promptStage: "inspect",
    busy: false,
    evidence: loadEvidence()
  };

  function loadEvidence() {
    try {
      return JSON.parse(localStorage.getItem(EVIDENCE_KEY) || "{}");
    } catch (err) {
      return {};
    }
  }
  function saveEvidence() {
    localStorage.setItem(EVIDENCE_KEY, JSON.stringify(state.evidence));
  }
  function recordEvidence(entry) {
    const list = state.evidence.events || [];
    list.push(Object.assign({ at: new Date().toISOString() }, entry));
    state.evidence.events = list;
    saveEvidence();
  }

  function show(id) {
    if (!screens.includes(id)) id = "landing";
    screens.forEach((name) => {
      const el = document.getElementById(name);
      if (el) el.classList.toggle("hidden", name !== id);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (id === "intro") renderIntro();
    if (id === "core") renderCore();
    if (id === "handover") renderHandover();
    if (id === "summary") renderSummary();
  }

  document.body.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-go]");
    if (!btn) return;
    if (btn.tagName === "A") return;
    event.preventDefault();
    if (btn.dataset.route) state.route = btn.dataset.route;
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
    if (data.result) {
      lines.push("reused_existing: " + data.result.reused_existing);
      lines.push("provider_invoked: " + data.result.provider_invoked);
      lines.push("output: " + data.result.output);
    }
    if (data.explanation) lines.push("\n" + data.explanation);
    if (data.meta && data.meta.teaching_note) lines.push("\n" + data.meta.teaching_note);
    return lines.join("\n");
  }

  async function runAction(path, body) {
    if (state.busy) return null;
    state.busy = true;
    try {
      let data;
      if (state.live) {
        const res = await fetch("/api/run/" + path, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body || {})
        });
        data = await res.json();
      } else if (path.startsWith("challenge/")) {
        const id = path.slice("challenge/".length);
        if (id === "stale_reset" || id.startsWith("stale_process") || id === "stale_compare") {
          data = {
            ok: false,
            mode: "sample",
            message: "Stepwise session needs live lab. Showing batched sample instead.",
            hint: "python scripts/tutorial_lab.py"
          };
          const sampleId =
            id === "stale_compare" || id.indexOf("process") >= 0
              ? "stale_sequential_faulty"
              : "stale_weak";
          try {
            const res = await fetch("assets/samples/" + sampleId + ".json", { cache: "no-store" });
            data = await res.json();
            data.mode = "sample";
          } catch (err) {
            data.error = String(err);
          }
        } else {
          const res = await fetch("assets/samples/" + id + ".json", { cache: "no-store" });
          data = await res.json();
        }
      } else {
        const res = await fetch("assets/lab_sample_" + path + ".json", { cache: "no-store" });
        data = await res.json();
        data.mode = "sample";
      }
      recordEvidence({
        kind: "run",
        path: path,
        mode: data.mode,
        ok: data.ok,
        expected_failure: !!data.expected_failure,
        challenge_id: data.challenge_id || path
      });
      return data;
    } finally {
      state.busy = false;
    }
  }

  /* ---------- Intro viewer ---------- */
  function pad3(n) {
    return String(n).padStart(3, "0");
  }

  function renderIntro() {
    const meta = state.introMeta;
    if (!meta) return;
    const indices = meta.slice_indices;
    const slider = document.getElementById("slice-slider");
    slider.max = String(indices.length - 1);
    slider.value = String(state.slicePos);
    const z = indices[state.slicePos];
    document.getElementById("slice-label").textContent =
      z + " / axis 2 (exported " + meta.slice_count_exported + " of " + meta.slice_count_total + " slices, step " + meta.export_step + ")";
    document.getElementById("intro-slice-caption").textContent =
      "Packaged case " + meta.case_id + " · " + meta.note;

    const mode = state.viewMode;
    const img = document.getElementById("intro-img");
    const overlayLayer = document.getElementById("intro-overlay-img");
    const baseKey = mode === "gt" || mode === "gt_overlay" ? "gt" : mode === "pred" ? "pred" : mode === "mri" ? "mri" : "mri";
    if (mode === "overlay" || mode === "gt_overlay") {
      img.src = "assets/intro_slices/mri_" + pad3(z) + ".png";
      const ov = mode === "overlay" ? "overlay_" : "gt_overlay_";
      overlayLayer.style.backgroundImage = "url(assets/intro_slices/" + ov + pad3(z) + ".png)";
      overlayLayer.style.opacity = String(state.opacity / 100);
      overlayLayer.classList.remove("hidden-layer");
    } else {
      const key = mode === "pred" ? "pred_" : mode === "gt" ? "gt_" : "mri_";
      img.src = "assets/intro_slices/" + key + pad3(z) + ".png";
      overlayLayer.classList.add("hidden-layer");
    }

    const legend = document.getElementById("intro-legend");
    legend.innerHTML = Object.keys(meta.labels)
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
      "<li>Outputs (when you run the demo):</li></ul><ul>" +
      meta.outputs_described.map((o) => "<li><code>" + o.path + "</code> — " + o.role + "</li>").join("") +
      "</ul>";
  }

  document.getElementById("slice-slider").addEventListener("input", (e) => {
    state.slicePos = Number(e.target.value);
    renderIntro();
  });
  document.getElementById("view-mode").addEventListener("change", (e) => {
    state.viewMode = e.target.value;
    renderIntro();
  });
  document.getElementById("opacity-slider").addEventListener("input", (e) => {
    state.opacity = Number(e.target.value);
    renderIntro();
  });

  /* ---------- Core stale challenge ---------- */
  const corePanel = document.getElementById("core-panel");
  const coreTerminal = document.getElementById("core-terminal");

  const STRONG_PROMPT =
    "Inspect the result-reuse logic. Add a regression test that processes two controlled cases with different reference predictions sequentially in the same output directory. Reload and copy the first saved output before the second invocation, then reload the second output and verify that each matches the corresponding reference. Do not merely compare output paths or assert that different inputs must produce different outputs. Demonstrate failure on the faulty implementation before fixing it. Do not modify reference predictions.";

  const STRONG_CODE =
    "def test_two_cases_same_output_dir(tmp_path):\n" +
    "    # Snapshot after A before calling B (same path may be returned).\n" +
    "    process(case_A, out_dir)  # faulty or corrected policy\n" +
    "    snap_A = out_dir / 'snap_A.nii.gz'; shutil.copy(out_dir / 'prediction.nii.gz', snap_A)\n" +
    "    process(case_B, out_dir)\n" +
    "    assert dice(load(out_dir / 'prediction.nii.gz'), ref_B) == 1.0\n" +
    "    # Optionally assert load(snap_A) still matches ref_A\n";

  function setCoreStep(n) {
    state.coreStep = Math.max(1, Math.min(6, n));
    document.querySelectorAll("#core-steps .step").forEach((el) => {
      const s = Number(el.dataset.step);
      el.classList.toggle("active", s === state.coreStep);
      el.classList.toggle("done", s < state.coreStep);
    });
    renderCore();
  }

  function renderCore() {
    let html = "";
    if (state.coreStep === 1) {
      html =
        "<h3>Request to the AI assistant</h3>" +
        "<pre class='prompt-box'>Skip segmentation if the prediction file already exists.</pre>" +
        "<h3>Plausible initial tests</h3>" +
        "<pre class='code-box'>def test_export_ok(case_dir, out_dir):\n" +
        "    result = process(case_dir, out_dir)  # fresh out_dir per case\n" +
        "    assert Path(result['output']).is_file()\n" +
        "    assert shape_matches(result, case_dir)\n" +
        "    assert labels_valid(result)\n</pre>" +
        "<button class='btn primary' type='button' id='run-stale-weak'>Run initial checks on faulty policy</button>" +
        "<p class='caption'>These use a fresh output directory per case, so they miss state carried between runs.</p>";
    } else if (state.coreStep === 2) {
      html =
        "<h3>Predict</h3>" +
        "<p>What happens if we process case A, then case B, using the <strong>same</strong> output directory?</p>" +
        "<div class='nav'>" +
        "<button class='btn' type='button' data-predict='ok'>B still gets B's correct result</button>" +
        "<button class='btn' type='button' data-predict='stale'>B may get A's old result</button>" +
        "</div><p id='predict-fb' class='caption'></p>";
    } else if (state.coreStep === 3) {
      html =
        "<h3>Guided run (shared output directory)</h3>" +
        "<p>Policy under test: <code>reuse_if_exists</code> (faulty teaching variant).</p>" +
        "<div class='nav'>" +
        "<button class='btn' type='button' id='stale-reset'>Reset exercise</button>" +
        "<button class='btn primary' type='button' id='stale-run-a'>Process case A</button>" +
        "<button class='btn primary' type='button' id='stale-run-b'>Process case B</button>" +
        "</div>" +
        "<p class='caption'>Session: " +
        (state.staleSession || "none — reset first") +
        "</p>";
    } else if (state.coreStep === 4) {
      html =
        "<h3>Compare evidence for case B</h3>" +
        "<p>Check whether the saved output matches B's reference (not merely that A and B differ).</p>" +
        "<button class='btn primary' type='button' id='stale-compare'>Inspect comparison table</button>";
    } else if (state.coreStep === 5) {
      html =
        "<h3>Stronger prompt &amp; test</h3>" +
        "<pre class='prompt-box'>" +
        escapeHtml(STRONG_PROMPT) +
        "</pre>" +
        "<div class='nav'><button class='btn' type='button' id='copy-strong'>Copy prompt</button>" +
        "<button class='btn primary' type='button' id='reveal-strong'>Reveal stronger test</button></div>" +
        "<pre id='strong-box' class='code-box hidden'></pre>" +
        "<button class='btn primary' type='button' id='run-reg-faulty'>Run regression on faulty policy</button>";
    } else {
      html =
        "<h3>Reference fix: always process current input and overwrite</h3>" +
        "<p>Minimal correct policy for this exercise. Optional advanced topic: safe cache keys must bind input content, model id, and config — a filename alone is not enough. This stand does not implement full cache invalidation.</p>" +
        "<p><em>Apply reference fix</em> switches to the prepared corrected implementation (not an in-browser AI edit).</p>" +
        "<button class='btn primary' type='button' id='run-reg-ok'>Run regression on corrected policy</button>" +
        "<p class='caption'>Verified here: weak tests can pass; sequential regression fails on reuse; passes after overwrite policy.</p>";
    }
    corePanel.innerHTML = html;
    wireCore();
  }

  function wireCore() {
    const term = coreTerminal;
    const showTerm = (data) => {
      term.classList.remove("hidden");
      term.textContent = formatResult(data);
    };
    const runWeak = document.getElementById("run-stale-weak");
    if (runWeak)
      runWeak.onclick = async () => {
        term.classList.remove("hidden");
        term.textContent = "Running…";
        showTerm(await runAction("challenge/stale_weak"));
      };
    corePanel.querySelectorAll("[data-predict]").forEach((btn) => {
      btn.onclick = () => {
        state.prediction = btn.dataset.predict;
        recordEvidence({ kind: "judgment", topic: "stale_predict", value: state.prediction });
        document.getElementById("predict-fb").textContent =
          state.prediction === "stale"
            ? "Recorded. Next: run A then B and inspect."
            : "Recorded. Next steps may surprise you.";
      };
    });
    const reset = document.getElementById("stale-reset");
    if (reset)
      reset.onclick = async () => {
        term.classList.remove("hidden");
        term.textContent = "Resetting…";
        const data = await runAction("challenge/stale_reset", {});
        state.staleSession = data.session_id || null;
        showTerm(data);
        renderCore();
      };
    const runA = document.getElementById("stale-run-a");
    if (runA)
      runA.onclick = async () => {
        if (!state.staleSession && state.live) {
          term.classList.remove("hidden");
          term.textContent = "Reset the exercise first.";
          return;
        }
        term.classList.remove("hidden");
        term.textContent = "Processing A…";
        showTerm(
          await runAction("challenge/stale_process_A", {
            session_id: state.staleSession,
            reuse_existing: true
          })
        );
      };
    const runB = document.getElementById("stale-run-b");
    if (runB)
      runB.onclick = async () => {
        term.classList.remove("hidden");
        term.textContent = "Processing B…";
        showTerm(
          await runAction("challenge/stale_process_B", {
            session_id: state.staleSession,
            reuse_existing: true
          })
        );
      };
    const cmp = document.getElementById("stale-compare");
    if (cmp)
      cmp.onclick = async () => {
        term.classList.remove("hidden");
        term.textContent = "Comparing…";
        if (state.live && state.staleSession) {
          showTerm(await runAction("challenge/stale_compare", { session_id: state.staleSession }));
        } else {
          showTerm(await runAction("challenge/stale_sequential_faulty"));
        }
      };
    const copyStrong = document.getElementById("copy-strong");
    if (copyStrong) copyStrong.onclick = () => copyText(STRONG_PROMPT, copyStrong);
    const reveal = document.getElementById("reveal-strong");
    if (reveal)
      reveal.onclick = () => {
        const box = document.getElementById("strong-box");
        box.textContent = STRONG_CODE;
        box.classList.remove("hidden");
        recordEvidence({ kind: "reveal", topic: "stale_strong_test" });
      };
    const regF = document.getElementById("run-reg-faulty");
    if (regF)
      regF.onclick = async () => {
        term.classList.remove("hidden");
        term.textContent = "Running…";
        showTerm(await runAction("challenge/stale_regression_faulty"));
      };
    const regOk = document.getElementById("run-reg-ok");
    if (regOk)
      regOk.onclick = async () => {
        term.classList.remove("hidden");
        term.textContent = "Running…";
        showTerm(await runAction("challenge/stale_regression_corrected"));
      };
  }

  document.getElementById("core-back").onclick = () => setCoreStep(state.coreStep - 1);
  document.getElementById("core-next").onclick = () => {
    if (state.coreStep >= 6) {
      show(state.route === "full" ? "challenges" : "summary");
      return;
    }
    setCoreStep(state.coreStep + 1);
  };

  /* ---------- Challenges menu ---------- */
  const challengeCopy = {
    level1_dice: {
      title: "Dice examples",
      req: "Identical→1, disjoint→0, partial closed-form; document empty-mask convention.",
      prompt: "Write deterministic dice_score unit tests; document both-empty → 1.0."
    },
    level1_shapes: {
      title: "Shape mismatch",
      req: "Reject mismatched shapes explicitly.",
      prompt: "Raise InputError on shape mismatch before mean_dice."
    },
    level1_invalid: {
      title: "Invalid inputs",
      req: "Missing file / constant image → clear InputError.",
      prompt: "Show load_mri InputError paths."
    },
    level2_geometry: {
      title: "Saved geometry (advanced)",
      req: "Optional affine teaching example.",
      prompt: "Compare saved affine to input after NIfTI round-trip."
    },
    level2_per_label: {
      title: "Mean vs per-label",
      req: "Mean Dice can hide one label collapsing.",
      prompt: "Assert mean≈0.8 with label-5 Dice=0."
    },
    level3_evidence: {
      title: "Provenance",
      req: "Arrays/geometry/provenance; bytes vs semantics.",
      prompt: "Explain semantic checks vs file-byte equality for NIfTI."
    }
  };

  document.querySelectorAll("[data-challenge]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.challenge;
      const info = challengeCopy[id];
      const detail = document.getElementById("challenge-detail");
      detail.classList.remove("hidden");
      detail.innerHTML =
        "<h3>" +
        info.title +
        "</h3><p><strong>Requirement:</strong> " +
        info.req +
        "</p><pre class='prompt-box'>" +
        escapeHtml(info.prompt) +
        "</pre><button class='btn primary' type='button' id='run-ch'>Run verification</button>";
      document.getElementById("run-ch").onclick = async () => {
        const term = document.getElementById("challenge-terminal");
        term.classList.remove("hidden");
        term.textContent = "Running…";
        term.textContent = formatResult(await runAction("challenge/" + id));
      };
    });
  });

  /* ---------- Handover ---------- */
  function renderHandover() {
    if (!state.content) return;
    document.getElementById("readme-incomplete").textContent = state.content.readme_incomplete;
    document.getElementById("readme-improved").textContent = state.content.readme_improved;
    document.getElementById("readme-improved-wrap").classList.toggle("hidden", !state.revealedReadme);
    const stages = ["inspect", "implement", "review"];
    const tabs = document.getElementById("prompt-tabs");
    tabs.innerHTML = stages
      .map((s) => {
        const active = state.promptStage === s ? "active" : "";
        return (
          '<button type="button" class="scenario-tab ' +
          active +
          '" data-stage="' +
          s +
          '">' +
          state.content.prompts[s].title.split("—")[0].trim() +
          "</button>"
        );
      })
      .join("");
    document.getElementById("prompt-text").textContent = state.content.prompts[state.promptStage].text;
    tabs.querySelectorAll("[data-stage]").forEach((btn) => {
      btn.onclick = () => {
        state.promptStage = btn.dataset.stage;
        renderHandover();
      };
    });
  }

  document.getElementById("reveal-readme").onclick = () => {
    state.revealedReadme = true;
    recordEvidence({ kind: "reveal", topic: "readme_improved" });
    const notes = document.getElementById("readme-notes").value.trim();
    if (notes) recordEvidence({ kind: "judgment", topic: "readme_notes", value: notes.slice(0, 400) });
    renderHandover();
  };
  document.getElementById("copy-readme-prompt").onclick = (e) =>
    copyText(state.content.readme_audit_prompt, e.currentTarget);
  document.getElementById("copy-stage-prompt").onclick = (e) =>
    copyText(state.content.prompts[state.promptStage].text, e.currentTarget);

  /* ---------- Summary ---------- */
  function renderSummary() {
    const events = state.evidence.events || [];
    const live = events.filter((e) => e.kind === "run" && e.mode === "live");
    const samples = events.filter((e) => e.kind === "run" && e.mode === "sample");
    const detected = events.filter((e) => e.expected_failure);
    const box = document.getElementById("summary-box");
    box.innerHTML =
      "<h3>Session evidence</h3><ul>" +
      "<li><strong>Checks executed live:</strong> " +
      (live.length ? live.map((e) => e.challenge_id || e.path).join(", ") : "none") +
      "</li>" +
      "<li><strong>Pre-recorded results inspected:</strong> " +
      (samples.length ? samples.map((e) => e.challenge_id || e.path).join(", ") : "none") +
      "</li>" +
      "<li><strong>Seeded defect detected (expected failure):</strong> " +
      (detected.length ? detected.map((e) => e.challenge_id).join(", ") : "none") +
      "</li>" +
      "<li><strong>Corrected behaviour verified:</strong> listed only if you ran stale_regression_corrected / sequential_corrected live</li>" +
      "<li><strong>Not verified:</strong> full nnU-Net inference, clinical performance, production readiness</li>" +
      "</ul><p>Research sharing ≠ production deployment ≠ clinical use.</p>";
  }

  function markdownSummary() {
    const events = state.evidence.events || [];
    return [
      "# Evidence summary",
      "",
      "- Live runs: " +
        events
          .filter((e) => e.mode === "live")
          .map((e) => e.challenge_id || e.path)
          .join(", "),
      "- Samples: " +
        events
          .filter((e) => e.mode === "sample")
          .map((e) => e.challenge_id || e.path)
          .join(", "),
      "- Expected failures: " + events.filter((e) => e.expected_failure).map((e) => e.challenge_id).join(", "),
      "",
      "## Not claimed",
      "- Clinical validation / production readiness / fresh model inference unless separately run",
      ""
    ].join("\n");
  }

  document.getElementById("copy-summary").onclick = (e) => copyText(markdownSummary(), e.currentTarget);
  document.getElementById("restart").onclick = () => {
    state.evidence = { events: [] };
    state.coreStep = 1;
    state.staleSession = null;
    state.revealedReadme = false;
    saveEvidence();
    show("landing");
  };

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      const prev = btn.textContent;
      btn.textContent = "Copied";
      setTimeout(() => {
        btn.textContent = prev;
      }, 1000);
    } catch (err) {
      btn.textContent = "Copy failed";
    }
  }

  Promise.all([
    fetch("assets/intro_meta.json").then((r) => r.json()),
    fetch("assets/tutorial_content.json?v=20260921b").then((r) => r.json())
  ])
    .then(([intro, content]) => {
      state.introMeta = intro;
      // Update prompts toward stale-reuse theme while keeping structure
      content.prompts = content.prompts || {};
      content.prompts.inspect = {
        title: "Stage 1 — Inspect",
        text:
          "Inspect result-reuse / output-directory logic in this teaching repo. Clarify whether an existing prediction.nii.gz is bound to input identity. Do not modify examples/case_001. Distinguish executed checks from proposals."
      };
      content.prompts.implement = {
        title: "Stage 2 — Implement",
        text: STRONG_PROMPT
      };
      content.prompts.review = {
        title: "Stage 3 — Review",
        text:
          "Review the diff for overwrite-vs-reuse. Confirm the sequential A→B regression fails on the faulty policy and passes on always-overwrite. Flag any README claim stronger than the tests."
      };
      state.content = content;
      renderIntro();
      renderHandover();
    })
    .catch((err) => {
      console.error(err);
      if (labBanner) {
        labBanner.className = "lab-banner sample";
        labBanner.textContent = "Failed to load intro assets. Run scripts/export_intro_slices.py and tutorial_lab.py.";
      }
    });

  probeLab();
})();
