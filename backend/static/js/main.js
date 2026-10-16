/* GreenShop — small progressive enhancements.
   Everything works without JS except: mobile menu, gallery switching,
   quantity steppers, tabs and dialogs. */
(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------------------------------------------------------------- nav */
  const navToggle = $(".nav-toggle");
  const nav = $("#primary-nav");
  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const open = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", String(!open));
      nav.dataset.open = String(!open);
    });
  }

  /* ------------------------------------------------------------- search */
  const searchToggle = $("[data-search-toggle]");
  const searchBar = $("#header-search");
  if (searchToggle && searchBar) {
    searchToggle.addEventListener("click", () => {
      const open = searchToggle.getAttribute("aria-expanded") === "true";
      searchToggle.setAttribute("aria-expanded", String(!open));
      searchBar.dataset.open = String(!open);
      if (!open) $("input", searchBar)?.focus();
    });
  }

  /* ------------------------------------------------------------ dialogs */
  const supported = typeof HTMLDialogElement !== "undefined";

  const openDialog = (dialog) => {
    if (!dialog) return;
    // showModal() throws InvalidStateError when the dialog is already up.
    if (dialog.open) {
      dialog.focus({ preventScroll: true });
      return;
    }
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    // Move focus to the dialog itself so the close button is not
    // ringed the moment the dialog appears (it still rings on Tab).
    if (dialog.hasAttribute("tabindex")) dialog.focus({ preventScroll: true });
  };

  const closeDialog = (dialog) => {
    if (!dialog) return;
    if (typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
  };

  const swapDialog = (dialog) => {
    if (!dialog) return;
    // Only one modal at a time: drop whatever else is open first.
    $$("dialog[open]").forEach((open) => {
      if (open !== dialog) closeDialog(open);
    });
    openDialog(dialog);
  };

  $$("[data-dialog]").forEach((trigger) => {
    // A <form data-dialog> must open on submit only — wiring it to "click"
    // would fire for every bubbled click inside the form (typing, coupon
    // reveal, payment options ...) and pop the dialog at random.
    if (trigger.tagName === "FORM") return;
    trigger.addEventListener("click", (event) => {
      const dialog = document.getElementById(trigger.dataset.dialog);
      if (!dialog) return;
      event.preventDefault();
      swapDialog(dialog);
    });
  });

  $$("dialog").forEach((dialog) => {
    $$("[data-dialog-close]", dialog).forEach((btn) =>
      btn.addEventListener("click", () => closeDialog(dialog))
    );
    // light-dismiss: click on the backdrop (the <dialog> element itself)
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeDialog(dialog);
    });
    if (dialog.dataset.autoshow === "true") openDialog(dialog);
  });

  if (!supported) {
    document.documentElement.classList.add("no-dialog");
  }

  /* --------------------------------------------------- password reveal */
  $$("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      if (!input) return;
      const reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      btn.setAttribute("aria-pressed", String(reveal));
      btn.setAttribute(
        "aria-label",
        reveal ? "Hide password" : "Show password"
      );
      const icon = $("img", btn);
      if (icon) {
        icon.src = reveal
          ? icon.src.replace("icon-eye-off", "icon-eye")
          : icon.src.replace(/icon-eye(?!-off)/, "icon-eye-off");
      }
    });
  });

  /* ----------------------------------------------------------- steppers */
  $$("[data-stepper]").forEach((stepper) => {
    const field = $("input, output", stepper);
    const read = () => parseInt(field.value ?? field.textContent, 10) || 0;
    const write = (value) => {
      const next = Math.max(1, Math.min(999, value));
      if ("value" in field) field.value = String(next);
      else field.textContent = String(next);
      stepper.dispatchEvent(new CustomEvent("step", { detail: next }));
    };

    $$("[data-step]", stepper).forEach((btn) => {
      btn.addEventListener("click", () => {
        write(read() + Number(btn.dataset.step));
      });
    });
  });

  /* ----------------------------------------------------------- gallery */
  const gallery = $("[data-gallery]");
  if (gallery) {
    const main = $("[data-gallery-main]", gallery);
    $$("[data-gallery-thumb]", gallery).forEach((thumb) => {
      thumb.addEventListener("click", () => {
        $$("[data-gallery-thumb]", gallery).forEach((t) =>
          t.setAttribute("aria-selected", "false")
        );
        thumb.setAttribute("aria-selected", "true");
        const img = $("img", thumb);
        if (main && img) {
          main.src = img.dataset.full || img.src;
          main.alt = img.alt;
        }
      });
    });
  }

  /* ------------------------------------------------------ tabs & toggles */
  $$("[data-tabs]").forEach((group) => {
    const buttons = $$('[role="tab"]', group);
    buttons.forEach((btn, index) => {
      btn.addEventListener("click", () => select(index));
      btn.addEventListener("keydown", (event) => {
        if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
        event.preventDefault();
        const dir = event.key === "ArrowRight" ? 1 : -1;
        const next = (index + dir + buttons.length) % buttons.length;
        select(next);
        buttons[next].focus();
      });
    });

    function select(active) {
      buttons.forEach((btn, i) => {
        const on = i === active;
        btn.setAttribute("aria-selected", String(on));
        btn.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(btn.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
    }
  });

  $$("[data-press-group]").forEach((group) => {
    $$("button", group).forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("button", group).forEach((b) =>
          b.setAttribute("aria-pressed", String(b === btn))
        );
      });
    });
  });

  $$("[data-select-toggle]").forEach((group) => {
    $$("button", group).forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("button", group).forEach((b) =>
          b.setAttribute("aria-selected", String(b === btn))
        );
      });
    });
  });

  /* ----------------------------------------------------------- cart row */
  $$("[data-remove-item]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr, li");
      if (!row) return;
      row.remove();
      const status = $("[data-cart-status]");
      if (status) status.textContent = "Item removed from your cart.";
    });
  });

  /* -------------------------------------------------------- price range */
  $$("[data-range]").forEach((wrap) => {
    const inputs = $$('input[type="range"]', wrap);
    if (inputs.length !== 2) return;
    const fill = $(".range__fill", wrap);
    const label = $("[data-range-label]", wrap);
    const min = Number(inputs[0].min);
    const max = Number(inputs[0].max);

    const paint = () => {
      const values = inputs.map((i) => Number(i.value));
      const [low, high] = [...values].sort((a, b) => a - b);
      const toPct = (v) => ((v - min) / (max - min)) * 100;
      if (fill) {
        fill.style.setProperty("--from", `${toPct(low)}%`);
        fill.style.setProperty("--span", `${toPct(high) - toPct(low)}%`);
      }
      if (label) label.textContent = `$${low} - $${high}`;
    };

    inputs.forEach((input, index) => {
      input.addEventListener("input", () => {
        const other = inputs[1 - index];
        const crosses =
          index === 0
            ? Number(input.value) > Number(other.value)
            : Number(input.value) < Number(other.value);
        if (crosses) input.value = other.value;
        paint();
      });
    });
    paint();
  });

  /* -------------------------------------------------------------- forms */
  $$("form[data-demo]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const status = $("[data-status]", form);
      if (status) {
        status.textContent = form.dataset.demo;
        status.focus?.();
      }
      const target = form.dataset.dialog
        ? document.getElementById(form.dataset.dialog)
        : null;
      if (target) swapDialog(target);
      else form.reset();
    });
  });

  /* ------------------------------------------- demo anchor stubs
     The mock has no backend, so these in-page anchors would otherwise
     jump nowhere. Each one gets a real, visible reaction instead. */

  // "Forgot Password?" -> the reset dialog shipped in the master template.
  const forgotDialog = $("#forgot-dialog");
  $$('a[href="#forgot"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      if (!forgotDialog) return;
      swapDialog(forgotDialog);
      $("#forgot-email", forgotDialog)?.focus({ preventScroll: true });
    });
  });

  // "Login with Google / Facebook" -> an honest inline note.
  $$('a[href="#google"], a[href="#facebook"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const wrap = link.closest(".auth-social");
      if (!wrap) return;
      const provider = link.getAttribute("href").slice(1);
      const label = provider.charAt(0).toUpperCase() + provider.slice(1);
      let note = wrap.nextElementSibling;
      if (!note || !note.hasAttribute("data-social-note")) {
        note = document.createElement("p");
        note.className = "form-status";
        note.setAttribute("data-social-note", "");
        note.setAttribute("role", "status");
        wrap.after(note);
      }
      note.textContent =
        label + " sign-in is a demo placeholder — no provider is connected.";
    });
  });

  // "Have a coupon code? Click here" -> reveal the coupon field.
  if (!document.getElementById("coupon-code")) {
    $$('a[href="#coupon-code"]').forEach((link) => {
      const panel = document.createElement("div");
      panel.className = "coupon coupon--reveal";
      panel.id = "coupon-reveal";
      panel.hidden = true;
      panel.innerHTML =
        '<div class="coupon__field">' +
        '<label for="coupon-code">Coupon Apply</label>' +
        '<input id="coupon-code" type="text" name="coupon" ' +
        'placeholder="Enter coupon code here..." autocomplete="off" />' +
        '<button type="button">Apply</button>' +
        "</div>" +
        '<p class="form-status" data-status role="status"></p>';
      link.after(panel);

      link.setAttribute("aria-expanded", "false");
      link.setAttribute("aria-controls", panel.id);

      link.addEventListener("click", (event) => {
        event.preventDefault();
        const reveal = panel.hidden;
        panel.hidden = !reveal;
        link.setAttribute("aria-expanded", String(reveal));
        if (reveal) $("input", panel)?.focus({ preventScroll: true });
      });

      $("button", panel)?.addEventListener("click", () => {
        const input = $("input", panel);
        const status = $("[data-status]", panel);
        const code = input.value.trim();
        if (!code) {
          status.textContent = "Enter a coupon code first.";
          input.focus();
          return;
        }
        status.textContent = 'Coupon "' + code + '" applied.';
      });
    });
  }

  /* -------------------------------------------- mobile app chrome -----
     Everything below only matters below 640px, where the app shell
     (bottom tab bar, floating action button, screen headers) replaces the
     desktop header. It is harmless on desktop. */

  // Mark the active destination in the bottom tab bar.
  const here = location.pathname.split("/").pop() || "index.html";
  $$(".appbar__link").forEach((link) => {
    const target = (link.getAttribute("href") || "").split(/[?#]/)[0];
    if (target && target === here) link.setAttribute("aria-current", "page");
  });

  // The filter square in the mobile search row reveals the filter panel.
  const filterToggle = $("[data-filter-toggle]");
  const filterPanel = document.getElementById("filters");
  if (filterToggle && filterPanel) {
    filterToggle.addEventListener("click", () => {
      const open = filterPanel.dataset.open === "true";
      filterPanel.dataset.open = String(!open);
      filterToggle.setAttribute("aria-expanded", String(!open));
    });
  }

  // Mobile shop tabs: mirror the ?sort= query onto the tab strip.
  const sort = new URLSearchParams(location.search).get("sort");
  const activeTab = sort === "new" ? "new" : sort === "sale" ? "sale" : "all";
  $$(".m-tabs__item").forEach((tab) => {
    if (tab.dataset.mTab !== activeTab) return;
    tab.classList.add("is-active");
    tab.setAttribute("aria-current", "page");
  });

  // The wishlist tab has no page in this build — say so instead of jumping
  // to a dead anchor.
  const appbarNote = $("[data-appbar-note]");
  let noteTimer;
  const say = (message) => {
    if (!appbarNote) return;
    appbarNote.textContent = message;
    clearTimeout(noteTimer);
    noteTimer = setTimeout(() => {
      appbarNote.textContent = "";
    }, 4000);
  };

  $$('a[href="#wishlist"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      say("Your wishlist is empty — this is a demo build.");
    });
  });

  // Wishlist heart on the mobile product screen.
  $$("[data-wishlist-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const on = btn.getAttribute("aria-pressed") === "true";
      btn.setAttribute("aria-pressed", String(!on));
      const path = $("path", btn);
      if (path) path.setAttribute("fill", on ? "none" : "currentColor");
      say(on ? "Removed from your wishlist." : "Added to your wishlist.");
    });
  });

  /* Keep the sticky "Login" button pointing at the right dialog target. */
  document.documentElement.classList.add("js");
})();
