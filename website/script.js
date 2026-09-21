(() => {
  const SCORE_KEY = "vibe_assess_scores_v1";

  const state = {
    use: null,
    testing: {},
    repro: {},
    lab: { live: null, lastAction: null },
    assess: {
      active: "weak",
      gallery: null,
      scores: loadScores(),
      compared: {}
    },
    pack: {
      active: "A",
      selected: null,
      bags: { A: [], B: [], C: [] },
      checked: { A: false, B: false, C: false },
      results: { A: null, B: null, C: null }
    }
  };

  function loadScores() {
    try {
      return JSON.parse(localStorage.getItem(SCORE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveScores() {
    localStorage.setItem(SCORE_KEY, JSON.stringify(state.assess.scores));
  }

  const uses = [
    { id: "personal", title: "Personal prototype", blurb: "Works on my laptop for exploration." },
    { id: "demo", title: "Live demo", blurb: "Show collaborators or a conference audience." },
    { id: "opensource", title: "Publication / open-source", blurb: "Others should install and reproduce." },
    { id: "clinical", title: "Clinical / production software", blurb: "Broader verification, validation and controls." }
  ];

  const testingItems = [
    { id: "smoke", tag: "SMOKE", title: "Smoke testing", text: "One example completes MRI → preprocess → model/cache → mask → saved result." },
    { id: "unit", tag: "UNIT", title: "Unit testing", text: "Check shapes, dtypes, valid labels and Dice on a known toy example." },
    { id: "integration", tag: "INTEGRATION", title: "Integration testing", text: "The full workflow works when components are combined on one sample case." },
    { id: "regression", tag: "REGRESSION", title: "Regression testing", text: "Before refactoring Dice = 0.82. After refactoring Dice = 0.57. Regression detected." },
    { id: "invalid", tag: "ROBUSTNESS", title: "Invalid-input testing", text: "Missing file, wrong shape, empty image, unsupported dtype or corrupted input should fail clearly." }
  ];

  const reproItems = [
    { id: "env", title: "Environment documented" },
    { id: "deps", title: "Dependency versions recorded" },
    { id: "ckpt", title: "Model checkpoint identified" },
    { id: "data", title: "Sample data / data version documented" },
    { id: "prep", title: "Preprocessing documented" },
    { id: "config", title: "Configuration recorded" },
    { id: "seed", title: "Random seed recorded where relevant" },
    { id: "code", title: "Code version recorded" },
    { id: "cmd", title: "Results reproducible from one documented command" }
  ];

  const packScenarios = {
    A: {
      id: "A",
      short: "Demo",
      title: "Conference / collaborator demo",
      bagLabel: "Demo bag",
      hint: "Pack only what makes a live demo trustworthy and easy to show.",
      pool: [
        "sample data",
        "README",
        "one-command demo",
        "smoke test",
        "cached expected output",
        "clinical validation",
        "regulatory traceability"
      ],
      needed: ["sample data", "README", "one-command demo", "smoke test", "cached expected output"],
      overkill: ["clinical validation", "regulatory traceability"],
      lesson: "A demo needs a runnable example and expected output — not a full clinical dossier."
    },
    B: {
      id: "B",
      short: "Open-source",
      title: "Publication / open-source repository",
      bagLabel: "Release bag",
      hint: "Pack what strangers need to install, run and cite your work.",
      pool: [
        "README",
        "environment",
        "fixed dependencies",
        "example data",
        "model checkpoint or download instructions",
        "reproduction script",
        "tests",
        "random seed",
        "licence",
        "citation",
        "limitations"
      ],
      needed: [
        "README",
        "environment",
        "fixed dependencies",
        "example data",
        "model checkpoint or download instructions",
        "reproduction script",
        "tests",
        "random seed",
        "licence",
        "citation",
        "limitations"
      ],
      overkill: [],
      lesson: "Open-source sharing is about reproducibility and clarity for other researchers."
    },
    C: {
      id: "C",
      short: "Clinical",
      title: "Clinical / production software",
      bagLabel: "Production bag",
      hint: "Pack software and governance evidence — much broader than a research demo.",
      pool: [
        "documented requirements",
        "verification",
        "validation",
        "requirement-test traceability",
        "risk controls",
        "software versioning",
        "change control",
        "audit/logging",
        "usability",
        "cybersecurity",
        "installation verification",
        "deployment environment",
        "system-level testing"
      ],
      needed: [
        "documented requirements",
        "verification",
        "validation",
        "requirement-test traceability",
        "risk controls",
        "software versioning",
        "change control",
        "audit/logging",
        "usability",
        "cybersecurity",
        "installation verification",
        "deployment environment",
        "system-level testing"
      ],
      overkill: [],
      lesson: "Clinical/production readiness is a software + risk + validation problem, not just a nicer demo."
    }
  };

  const recommendations = {
    personal: {
      covered: ["Runnable local prototype", "Example visualisation"],
      add: ["Smoke test", "Basic README", "Pin your environment"]
    },
    demo: {
      covered: ["Sample/cached example", "Visual overlay", "Short explanation"],
      add: ["One-command demo", "Smoke test", "Expected output note", "Clear limitations slide"]
    },
    opensource: {
      covered: ["README", "Example data", "Licence/citation placeholders"],
      add: ["Smoke + regression tests", "Reproduction script", "Pinned dependencies", "Model/version information", "Limitations section"]
    },
    clinical: {
      covered: ["Software testing concepts", "Reproducibility concepts"],
      add: ["Formal requirements & traceability", "Verification + validation plan", "Risk management", "Change control", "Security & audit logging", "Independent clinical evidence"]
    }
  };

  const screens = ["landing", "use", "testing", "repro", "lab", "assess", "scenarios", "summary"];

  function show(id) {
    screens.forEach((name) => {
      document.getElementById(name).classList.toggle("hidden", name !== id);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (id === "lab") refreshLabBanner();
    if (id === "assess") renderAssess();
  }

  document.querySelectorAll("[data-go]").forEach((btn) => {
    btn.addEventListener("click", () => show(btn.dataset.go));
  });

  const useGrid = document.getElementById("use-grid");
  useGrid.innerHTML = uses
    .map(
      (item) => `<button class="use-card" data-use="${item.id}"><strong>${item.title}</strong><span>${item.blurb}</span></button>`
    )
    .join("");
  useGrid.addEventListener("click", (event) => {
    const card = event.target.closest("[data-use]");
    if (!card) return;
    state.use = card.dataset.use;
    document.querySelectorAll(".use-card").forEach((el) => el.classList.toggle("selected", el === card));
    document.getElementById("use-next").disabled = false;
  });
  document.getElementById("use-next").addEventListener("click", () => show("testing"));

  const testingList = document.getElementById("testing-list");
  testingList.innerHTML = testingItems
    .map(
      (item) => `<div class="check-item" data-test="${item.id}"><span class="tag">${item.tag}</span><strong>${item.title}</strong><p>${item.text}</p></div>`
    )
    .join("");
  testingList.addEventListener("click", (event) => {
    const item = event.target.closest("[data-test]");
    if (!item) return;
    const id = item.dataset.test;
    state.testing[id] = !state.testing[id];
    item.classList.toggle("done", state.testing[id]);
  });

  const reproList = document.getElementById("repro-list");
  reproList.innerHTML = reproItems
    .map((item) => `<div class="check-item" data-repro="${item.id}"><strong>${item.title}</strong></div>`)
    .join("");
  reproList.addEventListener("click", (event) => {
    const item = event.target.closest("[data-repro]");
    if (!item) return;
    const id = item.dataset.repro;
    state.repro[id] = !state.repro[id];
    item.classList.toggle("done", state.repro[id]);
  });

  /* ---------- Lab ---------- */
  const labBanner = document.getElementById("lab-banner");
  const labTerminal = document.getElementById("lab-terminal");
  const labOverlayWrap = document.getElementById("lab-overlay-wrap");
  const labOverlay = document.getElementById("lab-overlay");

  async function probeLab() {
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      if (!res.ok) throw new Error("health failed");
      const data = await res.json();
      state.lab.live = !!data.ok;
    } catch {
      state.lab.live = false;
    }
    refreshLabBanner();
  }

  function refreshLabBanner() {
    if (state.lab.live === null) {
      labBanner.className = "lab-banner";
      labBanner.textContent = "Checking whether the local lab API is available…";
      return;
    }
    if (state.lab.live) {
      labBanner.className = "lab-banner live";
      labBanner.textContent = "Live lab connected — buttons run the real cached pipeline on this machine.";
    } else {
      labBanner.className = "lab-banner sample";
      labBanner.textContent =
        "Sample mode (static Pages or plain http.server). For a live run: python scripts/tutorial_lab.py";
    }
  }

  function formatLabResult(data) {
    const lines = [];
    lines.push(`$ ${data.command || data.action}`);
    lines.push(`mode: ${data.mode || "unknown"}`);
    lines.push(data.message || (data.ok ? "ok" : "failed"));
    if (data.mean_dice != null) lines.push(`mean_dice: ${data.mean_dice}`);
    if (data.metrics && typeof data.metrics === "object") {
      Object.entries(data.metrics).forEach(([k, v]) => {
        if (typeof v === "number") lines.push(`  ${k}: ${v}`);
      });
    }
    if (Array.isArray(data.checks)) {
      data.checks.forEach((c) => {
        lines.push(`${c.pass ? "PASS" : "FAIL"}  ${c.name}  —  ${c.detail}`);
      });
    }
    if (data.provenance) {
      lines.push("provenance:");
      Object.entries(data.provenance).forEach(([k, v]) => lines.push(`  ${k}: ${v}`));
    }
    if (data.error) lines.push(`error: ${data.error}`);
    return lines.join("\n");
  }

  async function runLabAction(action) {
    labTerminal.textContent = `Running ${action}…`;
    labOverlayWrap.classList.add("hidden");
    let data;
    if (state.lab.live) {
      try {
        const res = await fetch(`/api/run/${action}`, { method: "POST" });
        data = await res.json();
      } catch (err) {
        data = { ok: false, action, mode: "live", error: String(err), command: action };
      }
    } else {
      const res = await fetch(`assets/lab_sample_${action}.json`, { cache: "no-store" });
      data = await res.json();
    }
    state.lab.lastAction = action;
    labTerminal.textContent = formatLabResult(data);
    if (data.overlay_url) {
      labOverlay.src = `${data.overlay_url}?t=${Date.now()}`;
      labOverlayWrap.classList.remove("hidden");
    }
  }

  document.querySelectorAll("[data-lab]").forEach((btn) => {
    btn.addEventListener("click", () => runLabAction(btn.dataset.lab));
  });
  probeLab();

  /* ---------- Assess / score ---------- */
  const assessTabs = document.getElementById("assess-tabs");
  const assessPrompt = document.getElementById("assess-prompt");
  const assessCode = document.getElementById("assess-code");
  const assessRubric = document.getElementById("assess-rubric");
  const assessYourTotal = document.getElementById("assess-your-total");
  const assessFeedback = document.getElementById("assess-feedback");

  function activeCase() {
    if (!state.assess.gallery) return null;
    return state.assess.gallery.cases.find((c) => c.id === state.assess.active);
  }

  function ensureCaseScores(caseId) {
    if (!state.assess.scores[caseId]) state.assess.scores[caseId] = {};
    return state.assess.scores[caseId];
  }

  function yourTotal(caseId) {
    const scores = state.assess.scores[caseId] || {};
    return Object.values(scores).reduce((sum, v) => sum + (v ? 1 : 0), 0);
  }

  function renderAssess() {
    if (!state.assess.gallery) {
      assessPrompt.textContent = "Loading gallery…";
      return;
    }
    const c = activeCase();
    assessTabs.innerHTML = state.assess.gallery.cases
      .map((item) => {
        const active = item.id === state.assess.active ? "active" : "";
        const done = state.assess.compared[item.id] ? "done" : "";
        return `<button type="button" class="scenario-tab ${active} ${done}" data-assess-tab="${item.id}">${item.title}</button>`;
      })
      .join("");

    assessPrompt.textContent = c.prompt;
    assessCode.textContent = c.code;
    assessYourTotal.textContent = `${yourTotal(c.id)} / 6`;

    const user = ensureCaseScores(c.id);
    const compared = !!state.assess.compared[c.id];
    const key = c.answer_key.scores;

    assessRubric.innerHTML = state.assess.gallery.rubric
      .map((row) => {
        const val = user[row.id];
        let matchClass = "";
        if (compared && val !== undefined) {
          matchClass = Number(val) === Number(key[row.id]) ? "match-yes" : "match-no";
        }
        return `<div class="rubric-row ${matchClass}" data-rubric="${row.id}">
          <div><strong>${row.label}</strong><span class="hint">${row.hint}</span></div>
          <div class="rubric-toggle">
            <button type="button" data-val="1" class="${val === 1 ? "on-yes" : ""}">Yes</button>
            <button type="button" data-val="0" class="${val === 0 ? "on-no" : ""}">No</button>
          </div>
        </div>`;
      })
      .join("");

    if (compared) {
      const expected = c.answer_key.total;
      const yours = yourTotal(c.id);
      assessFeedback.classList.remove("hidden");
      assessFeedback.innerHTML = `
        <p class="score">Your score: ${yours}/6 · Answer key: ${expected}/6</p>
        <p>${c.critique}</p>
        <p class="caption">High scores still need a real run in the lab (or pytest) before you trust them.</p>
      `;
    } else {
      assessFeedback.classList.add("hidden");
      assessFeedback.innerHTML = "";
    }
  }

  assessTabs.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-assess-tab]");
    if (!tab) return;
    state.assess.active = tab.dataset.assessTab;
    renderAssess();
  });

  assessRubric.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-val]");
    if (!btn) return;
    const row = btn.closest("[data-rubric]");
    const id = row.dataset.rubric;
    const caseId = state.assess.active;
    ensureCaseScores(caseId)[id] = Number(btn.dataset.val);
    state.assess.compared[caseId] = false;
    saveScores();
    renderAssess();
  });

  document.getElementById("assess-reset").addEventListener("click", () => {
    state.assess.scores[state.assess.active] = {};
    state.assess.compared[state.assess.active] = false;
    saveScores();
    renderAssess();
  });

  document.getElementById("assess-compare").addEventListener("click", () => {
    state.assess.compared[state.assess.active] = true;
    renderAssess();
  });

  document.getElementById("copy-prompt").addEventListener("click", async () => {
    const c = activeCase();
    if (!c) return;
    try {
      await navigator.clipboard.writeText(c.prompt);
      document.getElementById("copy-prompt").textContent = "Copied";
      setTimeout(() => {
        document.getElementById("copy-prompt").textContent = "Copy prompt";
      }, 1200);
    } catch {
      document.getElementById("copy-prompt").textContent = "Copy failed";
    }
  });

  fetch("assets/prompt_gallery.json")
    .then((r) => r.json())
    .then((data) => {
      state.assess.gallery = data;
      renderAssess();
    })
    .catch(() => {
      assessPrompt.textContent = "Could not load prompt gallery.";
    });

  /* ---------- Pack ---------- */
  const tabsEl = document.getElementById("scenario-tabs");
  const poolEl = document.getElementById("item-pool");
  const bagEl = document.getElementById("item-bag");
  const bagDrop = document.getElementById("bag-drop");
  const feedbackEl = document.getElementById("pack-feedback");
  const nextBtn = document.getElementById("scenario-next");

  function activeScenario() {
    return packScenarios[state.pack.active];
  }

  function bagSet(id = state.pack.active) {
    return new Set(state.pack.bags[id]);
  }

  function renderTabs() {
    tabsEl.innerHTML = Object.values(packScenarios)
      .map((scenario) => {
        const active = scenario.id === state.pack.active ? "active" : "";
        const done = state.pack.checked[scenario.id] ? "done" : "";
        return `<button type="button" class="scenario-tab ${active} ${done}" data-scenario-tab="${scenario.id}" role="tab">${scenario.short}</button>`;
      })
      .join("");
  }

  function makeItemButton(label, inBag) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pack-item";
    btn.draggable = true;
    btn.dataset.item = label;
    btn.textContent = label;
    if (state.pack.selected === label) btn.classList.add("selected");

    const result = state.pack.results[state.pack.active];
    if (result && inBag) {
      if (result.overpacked.includes(label)) btn.classList.add("overkill");
      else if (result.correct.includes(label)) btn.classList.add("correct");
    }

    btn.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", label);
      event.dataTransfer.effectAllowed = "move";
      state.pack.selected = label;
    });

    btn.addEventListener("click", () => {
      if (state.pack.selected === label) state.pack.selected = null;
      else state.pack.selected = label;
      renderPack();
    });

    return btn;
  }

  function moveToBag(label) {
    const bag = state.pack.bags[state.pack.active];
    if (!bag.includes(label)) bag.push(label);
    state.pack.selected = null;
    state.pack.checked[state.pack.active] = false;
    state.pack.results[state.pack.active] = null;
    renderPack();
  }

  function moveToPool(label) {
    state.pack.bags[state.pack.active] = state.pack.bags[state.pack.active].filter((x) => x !== label);
    state.pack.selected = null;
    state.pack.checked[state.pack.active] = false;
    state.pack.results[state.pack.active] = null;
    renderPack();
  }

  function renderPack() {
    const scenario = activeScenario();
    const packed = bagSet();
    document.getElementById("bag-title").textContent = scenario.bagLabel;
    document.getElementById("bag-hint").textContent = scenario.hint;
    document.getElementById("pool-hint").textContent = state.pack.selected
      ? `Selected “${state.pack.selected}”. Tap the bag to pack it, or tap it again to cancel.`
      : "Tap an item, then tap the bag — or drag it across.";

    renderTabs();
    poolEl.innerHTML = "";
    bagEl.innerHTML = "";

    scenario.pool.forEach((label) => {
      if (!packed.has(label)) poolEl.appendChild(makeItemButton(label, false));
    });
    state.pack.bags[state.pack.active].forEach((label) => {
      bagEl.appendChild(makeItemButton(label, true));
    });

    if (state.pack.checked[state.pack.active] && state.pack.results[state.pack.active]) {
      showFeedback(state.pack.results[state.pack.active]);
    } else {
      feedbackEl.classList.add("hidden");
      feedbackEl.innerHTML = "";
    }

    const order = ["A", "B", "C"];
    const idx = order.indexOf(state.pack.active);
    const allChecked = order.every((id) => state.pack.checked[id]);
    if (allChecked || idx === order.length - 1) nextBtn.textContent = "See my summary";
    else if (state.pack.checked[state.pack.active]) nextBtn.textContent = `Next: ${packScenarios[order[idx + 1]].short}`;
    else nextBtn.textContent = "Next scenario";
  }

  function scoreBag() {
    const scenario = activeScenario();
    const packed = bagSet();
    const missing = scenario.needed.filter((item) => !packed.has(item));
    const overpacked = scenario.overkill.filter((item) => packed.has(item));
    const correct = scenario.needed.filter((item) => packed.has(item));
    const extras = [...packed].filter(
      (item) => !scenario.needed.includes(item) && !scenario.overkill.includes(item)
    );
    const total = scenario.needed.length + scenario.overkill.length;
    const points = correct.length + scenario.overkill.filter((item) => !packed.has(item)).length;
    const score = Math.round((points / Math.max(total, 1)) * 100);
    return { missing, overpacked, correct, extras, score, lesson: scenario.lesson, title: scenario.title };
  }

  function showFeedback(result) {
    feedbackEl.classList.remove("hidden");
    const missingHtml = result.missing.length
      ? `<p class="warn"><strong>Missing essentials</strong></p><ul>${result.missing.map((x) => `<li>${x}</li>`).join("")}</ul>`
      : `<p class="ok"><strong>All essentials packed.</strong></p>`;
    const hasOverkillOptions = packScenarios[state.pack.active].overkill.length > 0;
    const overHtml = result.overpacked.length
      ? `<p class="warn"><strong>Overpacked for this use</strong></p><ul>${result.overpacked.map((x) => `<li>${x}</li>`).join("")}</ul>`
      : hasOverkillOptions
        ? `<p class="ok"><strong>No clinical overkill in the bag.</strong></p>`
        : "";
    feedbackEl.innerHTML = `
      <p class="score">${result.score}% match · ${result.title}</p>
      ${missingHtml}
      ${overHtml}
      <p>${result.lesson}</p>
    `;
  }

  tabsEl.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-scenario-tab]");
    if (!tab) return;
    state.pack.active = tab.dataset.scenarioTab;
    state.pack.selected = null;
    renderPack();
  });

  bagDrop.addEventListener("dragover", (event) => {
    event.preventDefault();
    bagDrop.classList.add("drag-over");
  });
  bagDrop.addEventListener("dragleave", () => bagDrop.classList.remove("drag-over"));
  bagDrop.addEventListener("drop", (event) => {
    event.preventDefault();
    bagDrop.classList.remove("drag-over");
    const label = event.dataTransfer.getData("text/plain") || state.pack.selected;
    if (label) moveToBag(label);
  });
  bagDrop.addEventListener("click", (event) => {
    if (event.target.closest(".pack-item")) {
      moveToPool(event.target.closest(".pack-item").dataset.item);
      return;
    }
    if (state.pack.selected) moveToBag(state.pack.selected);
  });
  poolEl.addEventListener("dragover", (event) => event.preventDefault());
  poolEl.addEventListener("drop", (event) => {
    event.preventDefault();
    const label = event.dataTransfer.getData("text/plain");
    if (label) moveToPool(label);
  });

  document.getElementById("pack-reset").addEventListener("click", () => {
    state.pack.bags[state.pack.active] = [];
    state.pack.checked[state.pack.active] = false;
    state.pack.results[state.pack.active] = null;
    state.pack.selected = null;
    renderPack();
  });

  document.getElementById("pack-check").addEventListener("click", () => {
    state.pack.checked[state.pack.active] = true;
    state.pack.results[state.pack.active] = scoreBag();
    renderPack();
  });

  nextBtn.addEventListener("click", () => {
    const order = ["A", "B", "C"];
    const idx = order.indexOf(state.pack.active);
    const allChecked = order.every((id) => state.pack.checked[id]);
    if (allChecked || idx === order.length - 1) {
      renderSummary();
      show("summary");
      return;
    }
    state.pack.active = order[idx + 1];
    state.pack.selected = null;
    renderPack();
  });

  renderPack();

  document.getElementById("restart").addEventListener("click", () => {
    Object.assign(state, {
      use: null,
      testing: {},
      repro: {},
      lab: { live: state.lab.live, lastAction: null },
      assess: {
        active: "weak",
        gallery: state.assess.gallery,
        scores: {},
        compared: {}
      },
      pack: {
        active: "A",
        selected: null,
        bags: { A: [], B: [], C: [] },
        checked: { A: false, B: false, C: false },
        results: { A: null, B: null, C: null }
      }
    });
    localStorage.removeItem(SCORE_KEY);
    document.querySelectorAll(".use-card.selected, .check-item.done").forEach((el) => {
      el.classList.remove("selected", "done");
    });
    document.getElementById("use-next").disabled = true;
    labTerminal.textContent = "Ready. Choose an action above.";
    labOverlayWrap.classList.add("hidden");
    renderPack();
    renderAssess();
    show("landing");
  });

  function renderSummary() {
    const use = uses.find((item) => item.id === state.use) || uses[0];
    const rec = recommendations[use.id];
    const checkedTests = Object.entries(state.testing).filter(([, v]) => v).map(([k]) => k);
    const checkedRepro = Object.entries(state.repro).filter(([, v]) => v).map(([k]) => k);
    const demoResult = state.pack.results.A;
    const overpackedDemo = demoResult && demoResult.overpacked.length > 0;
    const packScores = ["A", "B", "C"]
      .map((id) => {
        const r = state.pack.results[id];
        return r
          ? `<li>${packScenarios[id].short}: ${r.score}%</li>`
          : `<li>${packScenarios[id].short}: not checked yet</li>`;
      })
      .join("");

    const assessLines =
      state.assess.gallery &&
      state.assess.gallery.cases
        .map((c) => {
          const yours = yourTotal(c.id);
          const expected = c.answer_key.total;
          const compared = state.assess.compared[c.id] ? ` (key ${expected}/6)` : "";
          return `<li>${c.title}: ${yours}/6${compared}</li>`;
        })
        .join("");

    const box = document.getElementById("summary-box");
    box.innerHTML = `
      <h3>Your target: ${use.title}</h3>
      <p><strong>Already covered (suggested baseline):</strong></p>
      <ul>${rec.covered.map((x) => `<li>${x}</li>`).join("")}</ul>
      <p><strong>Consider adding:</strong></p>
      <ul>${rec.add.map((x) => `<li>${x}</li>`).join("")}</ul>
      <p><strong>You marked ${checkedTests.length}/${testingItems.length} testing items and ${checkedRepro.length}/${reproItems.length} reproducibility items.</strong></p>
      <p><strong>Your AI-test scores:</strong></p>
      <ul>${assessLines || "<li>not scored yet</li>"}</ul>
      <p><strong>Packing scores:</strong></p>
      <ul>${packScores}</ul>
      ${
        use.id === "clinical"
          ? `<p>Clinical/production readiness is a much broader software, validation, risk-management and regulatory problem than this checklist.</p>`
          : `<p>A polished demo or open-source release still does not equal clinical readiness.</p>`
      }
      ${
        overpackedDemo
          ? `<p class="caption">You packed clinical/regulatory items into the demo bag. Those are usually unnecessary for a demo — and insufficient alone for clinical use.</p>`
          : ""
      }
    `;
  }
})();
