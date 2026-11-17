// Comportements communs à toutes les pages (sans React) : thème, menu,
// progression de lecture, lien actif, apparitions, compteurs, réseau animé,
// mémorisation de la langue et sommaire des documents.

const root = document.documentElement;
const params = new URLSearchParams(location.search);
const staticMode = params.has('static'); // ?static : tout afficher, sans animation
const reduceMotion = staticMode || matchMedia('(prefers-reduced-motion: reduce)').matches;

function store(key: string, value: string) {
  try { localStorage.setItem(key, value); } catch { /* stockage indisponible */ }
}

/* --- Thème ----------------------------------------------------------- */
document.getElementById('theme-toggle')?.addEventListener('click', () => {
  const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  store('aim2p-theme', next);
});

/* --- Langue : mémorise le choix et conserve l'ancre ------------------ */
document.querySelectorAll<HTMLAnchorElement>('[data-set-lang]').forEach((a) => {
  a.addEventListener('click', (e) => {
    const lang = a.dataset.setLang!;
    store('aim2p-lang', lang);
    if (a.getAttribute('aria-current') === 'true') { e.preventDefault(); return; }
    if (location.hash) { e.preventDefault(); location.href = a.href.split('#')[0] + location.hash; }
  });
});

/* --- Menu mobile ----------------------------------------------------- */
const nav = document.getElementById('main-nav');
const menuBtn = document.getElementById('menu-toggle');
if (nav && menuBtn) {
  const close = () => { nav.classList.remove('is-open'); menuBtn.setAttribute('aria-expanded', 'false'); };
  menuBtn.addEventListener('click', () => {
    const open = !nav.classList.contains('is-open');
    nav.classList.toggle('is-open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
  });
  nav.addEventListener('click', (e) => { if ((e.target as HTMLElement).closest('a')) close(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
}

/* --- Barre de progression de lecture -------------------------------- */
const bar = document.getElementById('scroll-progress');
let ticking = false;
function onScroll() {
  if (ticking || !bar) return;
  ticking = true;
  requestAnimationFrame(() => {
    const h = document.documentElement.scrollHeight - innerHeight;
    bar.style.transform = `scaleX(${h > 0 ? Math.min(1, scrollY / h) : 0})`;
    ticking = false;
  });
}
addEventListener('scroll', onScroll, { passive: true });
onScroll();

/* --- Lien actif du menu (accueil) ------------------------------------ */
const navLinks = Array.from(document.querySelectorAll<HTMLAnchorElement>('.main-nav a[data-nav]'));
const sectionObs = new IntersectionObserver((entries) => {
  for (const en of entries) {
    if (!en.isIntersecting) continue;
    navLinks.forEach((a) => a.classList.toggle('is-active', a.dataset.nav === en.target.id));
  }
}, { rootMargin: '-45% 0px -50% 0px' });
navLinks.forEach((a) => { const s = document.getElementById(a.dataset.nav!); if (s) sectionObs.observe(s); });

/* --- Apparitions au défilement -------------------------------------- */
const reveals = document.querySelectorAll('.reveal');
if (reduceMotion) {
  reveals.forEach((el) => el.classList.add('is-visible'));
} else {
  const revealObs = new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (en.isIntersecting) { en.target.classList.add('is-visible'); revealObs.unobserve(en.target); }
    }
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
  reveals.forEach((el) => revealObs.observe(el));
}

/* --- Compteurs du hero ---------------------------------------------- */
if (!reduceMotion) {
  const countObs = new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (!en.isIntersecting) continue;
      const el = en.target as HTMLElement, end = Number(el.dataset.count), t0 = performance.now();
      const frame = (now: number) => {
        const p = Math.min(1, (now - t0) / 1300);
        el.textContent = String(Math.round(end * (1 - (1 - p) ** 3)));
        if (p < 1) requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
      countObs.unobserve(el);
    }
  }, { threshold: 0.6 });
  document.querySelectorAll<HTMLElement>('[data-count]').forEach((c) => { c.textContent = '0'; countObs.observe(c); });
}

/* --- Réseau animé (section Afrique) --------------------------------- */
const net = document.getElementById('network') as HTMLCanvasElement | null;
if (net) {
  const ctx = net.getContext('2d')!;
  const COLORS = ['#F6B73C', '#EE5A3E', '#1FB28C', '#AEB9D6'];
  type Pt = { x: number; y: number; vx: number; vy: number; r: number; c: string };
  let pts: Pt[] = [], w = 0, h = 0, raf = 0, visible = false;

  const size = () => {
    const dpr = Math.min(2, devicePixelRatio || 1);
    w = net.clientWidth; h = net.clientHeight;
    net.width = Math.round(w * dpr); net.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = Math.round(Math.min(70, Math.max(26, (w * h) / 26000)));
    pts = Array.from({ length: count }, (_, i) => ({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.22, vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.8 + 1.2, c: COLORS[i % 4],
    }));
    draw();
  };
  const draw = () => {
    ctx.clearRect(0, 0, w, h);
    const max = 150;
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
        if (d >= max) continue;
        ctx.strokeStyle = `rgba(174,185,214,${(0.22 * (1 - d / max)).toFixed(3)})`;
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke();
      }
    }
    for (const p of pts) { ctx.fillStyle = p.c; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill(); }
  };
  const tick = () => {
    for (const p of pts) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
    }
    draw();
    raf = visible ? requestAnimationFrame(tick) : 0;
  };
  size();
  let rt = 0;
  addEventListener('resize', () => { clearTimeout(rt); rt = window.setTimeout(size, 200); });
  if (!reduceMotion) {
    new IntersectionObserver(([en]) => {
      visible = en.isIntersecting;
      if (visible && !raf) raf = requestAnimationFrame(tick);
    }).observe(net);
  }
}

/* --- Sommaire des documents : section en cours ---------------------- */
const tocLinks = Array.from(document.querySelectorAll<HTMLAnchorElement>('.toc a'));
if (tocLinks.length) {
  const tocObs = new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (!en.isIntersecting) continue;
      tocLinks.forEach((a) => a.classList.toggle('is-active', a.hash === '#' + en.target.id));
    }
  }, { rootMargin: '-20% 0px -70% 0px' });
  tocLinks.forEach((a) => { const h = document.getElementById(decodeURIComponent(a.hash.slice(1))); if (h) tocObs.observe(h); });
}
