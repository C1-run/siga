// siga landing — interactions engine (vanilla ES module)
// Lazy 3D scene start, scroll observers, counters, diff sync, FAQ, magnetic buttons.

const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ----------------------------------------------------
// 1. 3D SCENE LAZY START (after first paint + idle — keeps first render light;
//    skipped entirely on mobile / reduced-motion inside scene.js)
// ----------------------------------------------------
const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 200));
idle(() => import('./scene.js'));

// ----------------------------------------------------
// PARTICLE CANVAS (restored: max 46 particles, cursor repel within 80px)
// ----------------------------------------------------
const canvas = document.getElementById('particle-canvas');
if (canvas && !isReducedMotion) {
  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const numParticles = 46;
  const particles = [];
  const mouse = { x: -1000, y: -1000 };

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  for (let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      radius: Math.random() * 1.4 + 1.6,
      color: Math.random() > 0.35 ? 'rgba(250, 250, 250, 0.3)' : 'rgba(0, 255, 148, 0.32)',
    });
  }

  function animateParticles() {
    ctx.clearRect(0, 0, width, height);
    for (let i = 0; i < numParticles; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      const dx = p.x - mouse.x;
      const dy = p.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 80 && dist > 0) {
        const force = (80 - dist) / 80;
        p.x += (dx / dist) * force * 2.8;
        p.y += (dy / dist) * force * 2.8;
      }

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
    }
    requestAnimationFrame(animateParticles);
  }
  animateParticles();
}

// ----------------------------------------------------
// 2. HERO ENTRANCE — typewriter title, then staged reveal
//    (typing-mode: chars typed into existing spans, cursor follows)
// ----------------------------------------------------
const heroTitle = document.getElementById('hero-title');
const heroWords = document.querySelectorAll('.hero-3d-word');
const heroL2 = document.getElementById('hero-l2');
const heroSub = document.getElementById('hero-sub');
const verdictChips = document.querySelectorAll('.verdict-chip-3d');
const pulseLine = document.getElementById('hero-pulse-line');
const heroUnderline = document.getElementById('hero-underline');

function revealHeroChrome() {
  if (heroSub) heroSub.style.opacity = '1';
  verdictChips.forEach((c) => c.classList.add('revealed'));
  if (pulseLine) pulseLine.classList.add('drawn');
}

if (heroTitle && !isReducedMotion) {
  heroTitle.classList.add('typing-mode');

  // Build the typing plan from live DOM: [element-or-textnode, fullText]
  const line1Words = Array.from(heroWords);
  const weMakeIt = heroL2.querySelector('span'); // plain span "We make it "
  const confessSpan = heroL2.querySelector('.confess');
  const confessNode = confessSpan.childNodes[0]; // text node "confess."

  const plan = [
    ...line1Words.map((el) => ({ el, text: el.textContent, isNode: false, cps: 30 })),
    { el: weMakeIt, text: weMakeIt.textContent, isNode: false, cps: 30, pauseBefore: 280 },
    { el: confessNode, text: confessNode.nodeValue, isNode: true, cps: 12 }, // slower for drama
  ];

  // Clear all targets up front
  plan.forEach(({ el, isNode }) => {
    if (isNode) el.nodeValue = '';
    else el.textContent = '';
  });

  const cursor = document.createElement('span');
  cursor.className = 'hero-cursor';
  heroTitle.querySelector('#hero-l1').appendChild(cursor);

  let step = 0;
  function typeStep() {
    if (step >= plan.length) {
      // Typing done: underline draws, cursor lingers then fades, chrome reveals
      if (heroUnderline) heroUnderline.classList.add('drawn');
      revealHeroChrome();
      setTimeout(() => cursor.classList.add('done'), 1600);
      setTimeout(() => cursor.remove(), 2200);
      return;
    }
    const { el, text, isNode, cps, pauseBefore } = plan[step];
    const run = () => {
      let i = 0;
      // Park cursor right after the element being typed
      const anchor = isNode ? el.parentElement : el;
      anchor.insertAdjacentElement('afterend', cursor);
      (function tick() {
        i += 1;
        if (isNode) el.nodeValue = text.slice(0, i);
        else el.textContent = text.slice(0, i);
        if (i < text.length) {
          setTimeout(tick, 1000 / cps);
        } else {
          step += 1;
          setTimeout(typeStep, plan[step] && plan[step].pauseBefore ? plan[step].pauseBefore : 60);
        }
      })();
    };
    run();
  }
  setTimeout(typeStep, 420);
} else {
  // Reduced motion / no typing: instant reveal (original behavior)
  requestAnimationFrame(() => {
    heroWords.forEach((w) => w.classList.add('revealed'));
    if (heroL2) heroL2.classList.add('revealed');
    revealHeroChrome();
    if (heroUnderline) heroUnderline.classList.add('drawn');
  });
}

// ----------------------------------------------------
// 3. GRADIENT MESH BLOB ROTATION & SCROLL DRIFT
// ----------------------------------------------------
const meshBlob = document.getElementById('mesh-blob');
const scrollHint = document.getElementById('scroll-hint');

window.addEventListener(
  'scroll',
  () => {
    const scrolled = window.scrollY;
    if (meshBlob && !isReducedMotion) {
      const rot = (scrolled * 0.08) % 360;
      const yOffset = scrolled * 0.16;
      const xOffset = Math.sin(scrolled * 0.002) * 60;
      meshBlob.style.transform = `translate(${xOffset}px, ${yOffset}px) rotate(${rot}deg)`;
    }
    if (scrollHint) {
      scrollHint.style.opacity = scrolled > 90 ? '0' : '1';
    }
  },
  { passive: true }
);

// ----------------------------------------------------
// 4. DEATH ARCHIVE ANIMATIONS & OBSERVERS
// ----------------------------------------------------
const cardCaseA = document.getElementById('card-casea');
const caseaStamp = document.getElementById('casea-fail-stamp');
const caseaReported = document.getElementById('casea-reported-stat');
const caseaArrow = document.getElementById('casea-arrow-path');

if (cardCaseA) {
  const caseaObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          cardCaseA.classList.add('settled');

          setTimeout(() => {
            if (caseaStamp) caseaStamp.classList.add('landed');
          }, 300);

          setTimeout(() => {
            if (caseaReported) {
              caseaReported.classList.add('glitch-flash');
              setTimeout(() => {
                caseaReported.classList.add('cracked');
                caseaReported.textContent = '+15.30%';
                if (caseaArrow) caseaArrow.classList.add('drawn');
              }, 400);
            }
          }, 650);

          caseaObserver.unobserve(cardCaseA);
        }
      });
    },
    { threshold: 0.2 }
  );
  caseaObserver.observe(cardCaseA);
}

const cardCaseB = document.getElementById('card-caseb');
const casebLine = document.getElementById('caseb-reject-line');
const casebTestsGreen = document.getElementById('caseb-tests-green');

if (cardCaseB) {
  const casebObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          cardCaseB.classList.add('settled');

          setTimeout(() => {
            if (casebLine) casebLine.classList.add('drawn');
          }, 350);

          setTimeout(() => {
            cardCaseB.classList.add('recoil-shake');
          }, 600);

          cardCaseB.querySelectorAll('.count-target').forEach((ct) => runCounter(ct));

          setTimeout(() => {
            if (casebTestsGreen) {
              casebTestsGreen.classList.remove('stat-bright');
              casebTestsGreen.classList.add('stat-muted');
            }
          }, 1200);

          casebObserver.unobserve(cardCaseB);
        }
      });
    },
    { threshold: 0.25 }
  );
  casebObserver.observe(cardCaseB);
}

const cardCaseD = document.getElementById('card-cased');
if (cardCaseD) {
  const casedObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          cardCaseD.classList.add('settled');
          cardCaseD.querySelectorAll('.count-target').forEach((ct) => runCounter(ct));
          casedObserver.unobserve(cardCaseD);
        }
      });
    },
    { threshold: 0.2 }
  );
  casedObserver.observe(cardCaseD);
}

document.querySelectorAll('.svg-connector-line').forEach((line) => {
  const lineObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('drawn');
          lineObs.unobserve(e.target);
        }
      });
    },
    { threshold: 0.5 }
  );
  lineObs.observe(line);
});

// ----------------------------------------------------
// 5. SECTION 3: PAIN POINTS ENTRANCE
// ----------------------------------------------------
const painList = document.getElementById('pain-points-list');
if (painList) {
  const painObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          painList.querySelectorAll('.pain-row-entry').forEach((row) => row.classList.add('revealed'));
          painList.querySelectorAll('.divider-expand').forEach((div) => div.classList.add('drawn'));
          painObserver.unobserve(painList);
        }
      });
    },
    { threshold: 0.15 }
  );
  painObserver.observe(painList);
}

// ----------------------------------------------------
// 6. SECTION 4: FIVE CHECKS 3D ENTRANCE & MOUSE TILT
// ----------------------------------------------------
const checksGrid = document.getElementById('checks-grid');
if (checksGrid) {
  const checksObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          checksGrid.querySelectorAll('.check-card-entry').forEach((c) => c.classList.add('settled'));
          checksGrid.querySelectorAll('.check-top-border').forEach((b) => b.classList.add('drawn'));
          checksObserver.unobserve(checksGrid);
        }
      });
    },
    { threshold: 0.15 }
  );
  checksObserver.observe(checksGrid);
}

const tiltCards = document.querySelectorAll('.interactive-tilt-card');
if (!isReducedMotion) {
  tiltCards.forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = `perspective(600px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateZ(8px)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(600px) rotateY(0deg) rotateX(0deg) translateZ(0px)';
    });
  });
}

// ----------------------------------------------------
// 7. SECTION 5: MATRIX SEQUENTIAL ROW HIGHLIGHT & LINES
// ----------------------------------------------------
const matrixTable = document.getElementById('matrix-table');
if (matrixTable) {
  const matrixObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          document.querySelectorAll('.matrix-siga-col-line').forEach((line) => line.classList.add('drawn'));

          // Per-row: flash + check draws in sync, sequential down the column
          const rows = matrixTable.querySelectorAll('.matrix-row');
          const checks = matrixTable.querySelectorAll('.matrix-check');
          rows.forEach((row, idx) => {
            setTimeout(() => {
              row.classList.add('matrix-row-flash');
              if (checks[idx]) checks[idx].classList.add('drawn');
            }, idx * 140);
          });

          matrixObserver.unobserve(matrixTable);
        }
      });
    },
    { threshold: 0.25 }
  );
  matrixObserver.observe(matrixTable);
}

// ----------------------------------------------------
// 8. SECTION 6: PRICING ENTRANCE
// ----------------------------------------------------
const pricingGrid = document.getElementById('pricing-grid');
if (pricingGrid) {
  const pricingObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          pricingGrid.querySelectorAll('.pricing-card-entry').forEach((card) => card.classList.add('settled'));
          const popular = pricingGrid.querySelector('.pricing-popular-entry');
          if (popular) popular.classList.add('settled');
          pricingObs.unobserve(pricingGrid);
        }
      });
    },
    { threshold: 0.2 }
  );
  pricingObs.observe(pricingGrid);
}

// ----------------------------------------------------
// 9. SECTION 7: FAQ ENTRANCE & ACCORDION
// ----------------------------------------------------
const faqSection = document.getElementById('faq');
if (faqSection) {
  const faqObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          faqSection.querySelectorAll('.faq-entry').forEach((f) => f.classList.add('revealed'));
          setTimeout(() => {
            const first = faqSection.querySelector('.faq-item');
            if (first) first.classList.add('active');
            syncFaqAria();
          }, 500);
          faqObs.unobserve(faqSection);
        }
      });
    },
    { threshold: 0.2 }
  );
  faqObs.observe(faqSection);
}

// The accordion state lives in the .active class, which is visual only.
// Mirror it onto aria-expanded so the open/closed state is announced.
function syncFaqAria() {
  document.querySelectorAll('.faq-item').forEach((item) => {
    const btn = item.querySelector('.faq-toggle');
    if (btn) {
      btn.setAttribute('aria-expanded', item.classList.contains('active') ? 'true' : 'false');
    }
  });
}

const faqItems = document.querySelectorAll('.faq-item');
faqItems.forEach((item) => {
  const btn = item.querySelector('.faq-toggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const isActive = item.classList.contains('active');
      faqItems.forEach((i) => i.classList.remove('active'));
      if (!isActive) item.classList.add('active');
      syncFaqAria();
    });
  }
});

// ----------------------------------------------------
// 9.5 DEMO — terminal replay (types command, reveals output lines)
// ----------------------------------------------------
const termWindow = document.getElementById('term-window');
if (termWindow) {
  const termLines = Array.from(termWindow.querySelectorAll('.term-line'));
  const cmdEl = termWindow.querySelector('.term-cmd');
  const cmdText = cmdEl ? cmdEl.dataset.cmd : '';

  const finishReplay = () => {
    termWindow.classList.remove('replaying');
    termWindow.classList.add('replay-done');
    if (cmdEl) {
      cmdEl.classList.remove('typing');
      cmdEl.textContent = cmdText;
    }
  };

  if (isReducedMotion) {
    finishReplay();
  } else {
    const termObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        termObserver.unobserve(termWindow);
        termWindow.classList.add('replaying');

        const outputLines = termLines.slice(1); // line 0 is the prompt
        const revealOutput = (idx) => {
          if (idx >= outputLines.length) {
            finishReplay();
            return;
          }
          outputLines[idx].classList.add('shown');
          // verdict lines (tl-r) get a beat of emphasis before
          const isVerdict = outputLines[idx].classList.contains('tl-r');
          setTimeout(() => revealOutput(idx + 1), isVerdict ? 420 : 120);
        };

        if (cmdEl) {
          cmdEl.classList.add('typing');
          let i = 0;
          (function typeCmd() {
            i += 1;
            cmdEl.textContent = cmdText.slice(0, i);
            if (i < cmdText.length) setTimeout(typeCmd, 45);
            else setTimeout(() => revealOutput(0), 350);
          })();
        } else {
          revealOutput(0);
        }
      });
    }, { threshold: 0.35 });
    termObserver.observe(termWindow);
  }
}

// ----------------------------------------------------
// 10. CTA — SECTION 8: CTA 3D WORDS & MAGNETIC BUTTON RIPPLE
// ----------------------------------------------------
const ctaSection = document.getElementById('cta');
const ctaHeadline = document.getElementById('cta-headline');

if (ctaSection && ctaHeadline) {
  const ctaObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          ctaHeadline.querySelectorAll('.cta-word-3d').forEach((w) => w.classList.add('revealed'));
          startTypewriter();
          ctaObserver.unobserve(ctaSection);
        }
      });
    },
    { threshold: 0.25 }
  );
  ctaObserver.observe(ctaSection);
}

const magneticBtns = document.querySelectorAll('.magnetic-btn');
magneticBtns.forEach((btn) => {
  btn.addEventListener('mousemove', (e) => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    btn.style.transform = `translate(${x * 0.22}px, ${y * 0.22}px)`;
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'translate(0px, 0px)';
  });
  btn.addEventListener('click', (e) => {
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.classList.add('btn-ripple');
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
});

function startTypewriter() {
  const targetText = 'First audit report: FAIL (on ourselves)';
  const targetEl = document.getElementById('typewriter-text');
  if (!targetEl || targetEl.dataset.typed) return;
  targetEl.dataset.typed = 'true';

  let idx = 0;
  function typeChar() {
    if (idx < targetText.length) {
      targetEl.textContent += targetText.charAt(idx);
      idx++;
      setTimeout(typeChar, 45);
    }
  }
  setTimeout(typeChar, 300);
}

// ----------------------------------------------------
// 11. COUNTER FUNCTION
// ----------------------------------------------------
function runCounter(el) {
  if (el.dataset.counted) return;
  el.dataset.counted = 'true';

  const target = parseFloat(el.dataset.target);
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const isDecimal = String(el.dataset.target).includes('.');
  const duration = 950;
  const start = performance.now();

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(1, elapsed / duration);
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = target * ease;

    if (isDecimal) {
      el.textContent = `${prefix}${current.toFixed(2)}${suffix}`;
    } else {
      el.textContent = `${prefix}${Math.round(current)}${suffix}`;
    }

    if (progress < 1) {
      requestAnimationFrame(update);
    } else if (isDecimal) {
      el.textContent = `${prefix}${target.toFixed(2)}${suffix}`;
    } else {
      el.textContent = `${prefix}${target}${suffix}`;
    }
  }
  requestAnimationFrame(update);
}

// ----------------------------------------------------
// 12. SYNCHRONIZED CODE DIFF LINE HOVER + AST SCAN MOTION
// ----------------------------------------------------
const diffContainer = document.getElementById('casea-sync-diff');
if (diffContainer) {
  const diffLines = diffContainer.querySelectorAll('.diff-code-line');
  const linesPanelA = diffContainer.querySelectorAll('#diff-panel-a .diff-code-line');
  const linesPanelB = diffContainer.querySelectorAll('#diff-panel-b .diff-code-line');
  let diffHovering = false;

  function clearDiffHighlights() {
    diffLines.forEach((line) => {
      line.classList.remove('synced-highlight-neutral', 'synced-highlight-leak', 'synced-highlight-fix');
    });
  }

  function highlightLeakGroup() {
    linesPanelA.forEach((aLine) => {
      if (aLine.getAttribute('data-sync-group') === 'leak') {
        aLine.classList.add('synced-highlight-leak');
      }
    });
    linesPanelB.forEach((bLine) => {
      if (bLine.getAttribute('data-sync-group') === 'leak') {
        bLine.classList.add('synced-highlight-fix');
      }
    });
  }

  diffLines.forEach((line) => {
    line.addEventListener('mouseenter', () => {
      clearDiffHighlights();
      const group = line.getAttribute('data-sync-group');

      if (group === 'leak') {
        highlightLeakGroup();
      } else {
        diffContainer
          .querySelectorAll(`.diff-code-line[data-sync-group="${group}"]`)
          .forEach((matchedLine) => matchedLine.classList.add('synced-highlight-neutral'));
      }
    });
  });

  diffContainer.addEventListener('mouseenter', () => { diffHovering = true; });
  diffContainer.addEventListener('mouseleave', () => { diffHovering = false; clearDiffHighlights(); });

  // --- scan motion: staggered reveal + periodic sweep + idle leak pulse ---
  if (!isReducedMotion) {
    diffContainer.classList.add('scan-anim');
    [linesPanelA, linesPanelB].forEach((list) => {
      list.forEach((line, i) => line.style.setProperty('--line-i', i));
    });

    const SCAN_PERIOD = 7000;
    const SCAN_SWEEP_MS = 2300;

    function runScanCycle() {
      if (diffHovering || document.hidden) return;
      diffContainer.classList.add('scanning');
      // pulse leak lines when the sweep reaches mid-panel
      setTimeout(() => {
        if (!diffHovering) highlightLeakGroup();
      }, SCAN_SWEEP_MS / 2);
      setTimeout(() => {
        diffContainer.classList.remove('scanning');
        if (!diffHovering) clearDiffHighlights();
      }, SCAN_SWEEP_MS);
    }

    const scanIO = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            diffContainer.classList.add('revealed');
            setTimeout(runScanCycle, 900);
            setInterval(runScanCycle, SCAN_PERIOD);
            scanIO.unobserve(diffContainer);
          }
        });
      },
      { threshold: 0.35 }
    );
    scanIO.observe(diffContainer);
  }
}

// ----------------------------------------------------
// 13. WAITLIST FORM (placeholder endpoint — logs only)
// ----------------------------------------------------
const waitlistForm = document.getElementById('waitlist-form');
const waitlistMsg = document.getElementById('waitlist-msg');

if (waitlistForm && waitlistMsg) {
  waitlistForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = waitlistForm.email.value.trim();
    const btn = waitlistForm.querySelector('button[type="submit"]');
    const originalText = btn.querySelector('span').textContent;

    waitlistMsg.textContent = '';
    waitlistMsg.className = 'waitlist-msg';
    btn.querySelector('span').textContent = '...';
    btn.disabled = true;

    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `email=${encodeURIComponent(email)}`,
      });
      const data = await res.json();

      if (data.ok) {
        waitlistMsg.textContent = data.message;
        waitlistMsg.classList.add('success');
        waitlistForm.reset();
      } else {
        waitlistMsg.textContent = data.error === 'invalid_email' ? 'Please enter a valid email address.' : 'Something went wrong. Try again.';
        waitlistMsg.classList.add('error');
      }
    } catch (err) {
      waitlistMsg.textContent = 'Network error. Try again.';
      waitlistMsg.classList.add('error');
    } finally {
      btn.querySelector('span').textContent = originalText;
      btn.disabled = false;
    }
  });
}

// ----------------------------------------------------
// DEBUG OVERLAY (?debug=1) — self-reporting diagnostics for the 3D scene
// ----------------------------------------------------
if (new URLSearchParams(window.location.search).has('debug')) {
  setTimeout(() => {
    const c = document.getElementById('three-canvas');
    let webgl2 = false;
    try {
      webgl2 = !!document.createElement('canvas').getContext('webgl2');
    } catch (e) {}
    const d = window.__diag || { errors: ['__diag missing'], scene: 'unknown' };
    const lines = [
      `scene: ${d.scene}`,
      `viewport: ${window.innerWidth}x${window.innerHeight}`,
      `mobileMQ: ${window.matchMedia('(max-width: 768px)').matches}`,
      `coarsePointer: ${window.matchMedia('(pointer: coarse)').matches}`,
      `reducedMotion: ${window.matchMedia('(prefers-reduced-motion: reduce)').matches}`,
      `webgl2: ${webgl2}`,
      `canvas: ${c ? c.width + 'x' + c.height + ' / ' + getComputedStyle(c).display : 'MISSING'}`,
      `errors: ${d.errors.length ? d.errors.join(' | ') : 'none'}`,
    ];
    const el = document.createElement('pre');
    el.style.cssText =
      'position:fixed;left:8px;bottom:8px;z-index:99999;background:#000;border:1px solid #00ff94;color:#00ff94;font:12px/1.6 JetBrains Mono,monospace;padding:10px 12px;pointer-events:none;white-space:pre-wrap;max-width:92vw;margin:0';
    el.textContent = lines.join('\n');
    document.body.appendChild(el);
  }, 2500);
}
