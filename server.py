from flask import Flask, request, jsonify, render_template_string
from collections import deque

app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Orchard Simulation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,400&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
  --sky-top: #1a0a2e;
  --sky-bot: #0d1f3c;
  --ground: #1a3d1a;
  --ground-hi: #2a5c2a;
  --leaf-dark: #1e5c1e;
  --leaf-mid: #2d7a2d;
  --leaf-hi: #3da03d;
  --trunk: #5c3010;
  --apple-red: #e8373e;
  --apple-orange: #f07840;
  --crate-wood: #c8924e;
  --crate-dark: #8b5e20;
  --truck-body: #d44f28;
  --truck-cab: #b03518;
  --ink: #f0ead8;
  --ink-dim: rgba(240,234,216,0.45);
  --accent: #e8c060;
  --accent2: #7ce8a0;
  --p0-col: #4cc9f0;
  --p1-col: #f77f2a;
  --p2-col: #b07ef0;
  --loader-col: #e84060;
  --panel-bg: rgba(255,255,255,0.04);
  --panel-border: rgba(255,255,255,0.09);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0c0c18;
  color: var(--ink);
  font-family: 'DM Mono', monospace;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

/* ── HEADER ── */
header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 2rem;
  border-bottom: 1px solid var(--panel-border);
  background: rgba(12,12,24,0.92);
  position: sticky; top: 0; z-index: 100;
  backdrop-filter: blur(12px);
}
.header-left { display: flex; align-items: baseline; gap: 0.75rem; }
header h1 {
  font-family: 'Fraunces', serif;
  font-size: 1.35rem;
  color: var(--accent);
  letter-spacing: 0.01em;
  font-style: italic;
}
.header-sub { font-size: 11px; color: var(--ink-dim); letter-spacing: 0.12em; text-transform: uppercase; }
#pill {
  font-size: 11px; font-weight: 500; padding: 4px 14px; border-radius: 20px;
  background: rgba(120,200,120,0.12); border: 1px solid rgba(120,200,120,0.35); color: #7ce8a0;
  transition: all 0.4s; letter-spacing: 0.08em;
}
#pill.running { background: rgba(232,192,96,0.12); border-color: rgba(232,192,96,0.4); color: var(--accent); }
#pill.done    { background: rgba(76,201,240,0.12);  border-color: rgba(76,201,240,0.4);  color: var(--p0-col); }

/* ── MAIN LAYOUT ── */
main {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 0;
  flex: 1;
}

/* ── SCENE ── */
.scene-col {
  display: flex; flex-direction: column; padding: 1.25rem 1.25rem 1.25rem 2rem;
  gap: 1.25rem;
}
#scene-wrap {
  border-radius: 14px; overflow: hidden;
  border: 1px solid var(--panel-border);
  background: linear-gradient(175deg, #1a0a2e 0%, #0d1f3c 40%, #0d2010 100%);
  position: relative;
}
#main-svg { display: block; width: 100%; }

/* ── ZZZ ANIMATION ── */
@keyframes zFloat {
  0%   { opacity: 0.9; transform: translateY(0)   scale(1);   }
  100% { opacity: 0;   transform: translateY(-22px) scale(0.5); }
}
.zzz { animation: zFloat 1.5s ease-in infinite; }
.zzz:nth-child(2) { animation-delay: 0.4s; }
.zzz:nth-child(3) { animation-delay: 0.8s; }

/* Picker carry-fruit bounce */
@keyframes fruitBounce {
  0%,100% { transform: translateY(0); }
  50%     { transform: translateY(-3px); }
}
.fruit-carry { animation: fruitBounce 0.45s ease-in-out infinite; }

/* ── THREAD BADGES ── */
.badges-row {
  display: flex; gap: 0.6rem; flex-wrap: wrap;
}
.tbadge {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 8px; font-size: 11px; font-family: 'DM Mono', monospace;
  border: 1px solid; transition: all 0.3s; cursor: default;
  letter-spacing: 0.04em;
}
.dot { width: 7px; height: 7px; border-radius: 50%; transition: background 0.3s; flex-shrink: 0; }
.tbadge.idle     { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.12); color: var(--ink-dim); }
.tbadge.idle     .dot { background: #444; }
.tbadge.active   { background: rgba(124,232,160,0.08); border-color: rgba(124,232,160,0.35); color: #7ce8a0; }
.tbadge.active   .dot { background: #7ce8a0; box-shadow: 0 0 6px #7ce8a066; }
.tbadge.waiting  { background: rgba(232,192,96,0.08);  border-color: rgba(232,192,96,0.35);  color: var(--accent); }
.tbadge.waiting  .dot { background: var(--accent); }
.tbadge.sleeping { background: rgba(136,160,255,0.07); border-color: rgba(136,160,255,0.28); color: #aabcff; }
.tbadge.sleeping .dot { background: #8899ff; box-shadow: 0 0 5px #8899ff55; }
.tbadge.done     { background: rgba(100,100,100,0.06); border-color: rgba(100,100,100,0.18); color: #555; }
.tbadge.done     .dot { background: #333; }

/* ── SIDE PANEL ── */
.side-col {
  border-left: 1px solid var(--panel-border);
  display: flex; flex-direction: column; gap: 0;
  overflow: hidden;
}
.side-section {
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid var(--panel-border);
}
.side-label {
  font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--ink-dim); margin-bottom: 0.75rem;
}

/* Stats */
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.stat-box {
  background: var(--panel-bg); border: 1px solid var(--panel-border);
  border-radius: 10px; padding: 0.7rem 0.9rem;
}
.stat-val { font-size: 26px; font-family: 'Fraunces', serif; color: var(--ink); line-height: 1; margin-bottom: 3px; }
.stat-lbl { font-size: 10px; color: var(--ink-dim); letter-spacing: 0.1em; text-transform: uppercase; }

/* Progress */
.prog-bar { height: 5px; background: rgba(255,255,255,0.07); border-radius: 3px; overflow: hidden; margin-top: 6px; }
.prog-fill { height: 100%; background: linear-gradient(90deg, var(--accent2), var(--p0-col)); border-radius: 3px; transition: width 0.5s ease; width: 0%; }
.prog-nums { display: flex; justify-content: space-between; font-size: 11px; color: var(--ink-dim); margin-top: 5px; }

/* Log */
.log-wrap {
  flex: 1; overflow-y: auto; padding: 0.9rem 1.25rem;
  scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent;
}
.log-wrap h3 { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-dim); margin-bottom: 0.75rem; position: sticky; top: 0; background: #0c0c18; padding: 4px 0 8px; }
.log-entry {
  display: flex; gap: 8px; align-items: flex-start;
  font-size: 11px; line-height: 1.55; color: rgba(240,234,216,0.6);
  padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.log-entry:last-child { border-bottom: none; }
.log-tag {
  font-size: 9px; padding: 2px 6px; border-radius: 4px;
  flex-shrink: 0; margin-top: 2px; font-weight: 500; letter-spacing: 0.05em;
  font-family: 'DM Mono', monospace;
}
.lt-p0     { background: rgba(76,201,240,0.15);  color: var(--p0-col); }
.lt-p1     { background: rgba(247,127,42,0.15);  color: var(--p1-col); }
.lt-p2     { background: rgba(176,126,240,0.15); color: var(--p2-col); }
.lt-loader { background: rgba(232,64,96,0.15);   color: var(--loader-col); }
</style>
</head>
<body>
<header>
  <div class="header-left">
    <h1>Orchard Simulation</h1>
    <span class="header-sub">Concurrent thread visualiser</span>
  </div>
  <div id="pill">Waiting…</div>
</header>

<main>
  <div class="scene-col">

    <div id="scene-wrap">
    <svg id="main-svg" viewBox="0 0 920 440" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="moonGlow" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stop-color="#fffbe0" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="#fffbe0" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="leafG" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#3da03d"/>
        <stop offset="100%" stop-color="#1e5c1e"/>
      </linearGradient>
      <linearGradient id="trunkG" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stop-color="#3a1a06"/>
        <stop offset="50%"  stop-color="#5c3010"/>
        <stop offset="100%" stop-color="#3a1a06"/>
      </linearGradient>
      <linearGradient id="groundG" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="#1a3d1a"/>
        <stop offset="100%" stop-color="#0d200d"/>
      </linearGradient>
      <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="4" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="8" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>

    <!-- Sky -->
    <rect width="920" height="440" fill="url(#skyGrad)"/>
    <defs>
      <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1a0a2e"/>
        <stop offset="60%" stop-color="#0d1f3c"/>
        <stop offset="100%" stop-color="#0d2a18"/>
      </linearGradient>
    </defs>

    <!-- Stars -->
    <g opacity="0.7" fill="white">
      <circle cx="50"  cy="28" r="1"/>  <circle cx="120" cy="45" r="0.8"/>
      <circle cx="200" cy="20" r="1.2"/><circle cx="280" cy="55" r="0.9"/>
      <circle cx="350" cy="18" r="1"/>  <circle cx="450" cy="35" r="0.8"/>
      <circle cx="520" cy="15" r="1.2"/><circle cx="600" cy="42" r="1"/>
      <circle cx="680" cy="22" r="0.9"/><circle cx="760" cy="50" r="1.1"/>
      <circle cx="840" cy="28" r="0.8"/><circle cx="900" cy="38" r="1"/>
      <circle cx="85"  cy="65" r="0.7"/><circle cx="170" cy="72" r="0.9"/>
      <circle cx="320" cy="68" r="0.8"/><circle cx="700" cy="68" r="1"/>
      <circle cx="800" cy="60" r="0.8"/><circle cx="875" cy="70" r="1.1"/>
    </g>

    <!-- Moon glow -->
    <circle cx="800" cy="55" r="60" fill="url(#moonGlow)"/>
    <circle cx="800" cy="55" r="24" fill="#fffde8" opacity="0.88"/>
    <circle cx="808" cy="50" r="18" fill="#1a0a2e" opacity="0.22"/>

    <!-- Ground -->
    <rect x="0" y="330" width="920" height="110" fill="url(#groundG)"/>
    <line x1="0" y1="333" x2="920" y2="333" stroke="#2a5c2a" stroke-width="1.5" opacity="0.6"/>

    <!-- Path dirt -->
    <ellipse cx="490" cy="345" rx="220" ry="11" fill="#3a2a0a" opacity="0.25"/>

    <!-- ══ TREE ══ (centred at x=155) -->
    <g id="tree">
      <!-- Shadow -->
      <ellipse cx="155" cy="336" rx="65" ry="13" fill="#000" opacity="0.2"/>
      <!-- Trunk -->
      <path d="M142,330 C140,270 143,215 155,195 C167,215 170,270 168,330 Z" fill="url(#trunkG)"/>
      <!-- Branch left -->
      <path d="M155,235 Q108,210 80,185" stroke="#3a1a06" stroke-width="9" fill="none" stroke-linecap="round"/>
      <!-- Branch right -->
      <path d="M155,235 Q202,210 230,185" stroke="#3a1a06" stroke-width="9" fill="none" stroke-linecap="round"/>
      <!-- Branch up -->
      <path d="M155,215 Q148,178 152,152" stroke="#3a1a06" stroke-width="7" fill="none" stroke-linecap="round"/>
      <!-- Foliage layers -->
      <ellipse cx="155" cy="168" rx="78" ry="65" fill="#1e5c1e"/>
      <ellipse cx="88"  cy="185" rx="55" ry="45" fill="#1e5c1e"/>
      <ellipse cx="222" cy="182" rx="55" ry="45" fill="#1e5c1e"/>
      <ellipse cx="128" cy="128" rx="48" ry="40" fill="#2d7a2d"/>
      <ellipse cx="182" cy="128" rx="48" ry="40" fill="#2d7a2d"/>
      <ellipse cx="155" cy="115" rx="40" ry="34" fill="#3da03d"/>
      <ellipse cx="155" cy="112" rx="28" ry="24" fill="#4ab84a" opacity="0.5"/>
      <!-- Moonlight highlight on leaves -->
      <ellipse cx="195" cy="125" rx="22" ry="14" fill="rgba(255,253,220,0.06)"/>
    </g>

    <!-- ══ FRUITS ON TREE ══ -->
    <g id="fruits">
      <circle class="fruit" id="tf0"  cx="138" cy="148" r="9"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf1"  cx="162" cy="133" r="8"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf2"  cx="185" cy="143" r="9"  fill="#f07840" stroke="#a04410" stroke-width="1.5"/>
      <circle class="fruit" id="tf3"  cx="120" cy="165" r="8"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf4"  cx="198" cy="160" r="8"  fill="#f07840" stroke="#a04410" stroke-width="1.5"/>
      <circle class="fruit" id="tf5"  cx="148" cy="175" r="9"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf6"  cx="172" cy="170" r="8"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf7"  cx="103" cy="180" r="9"  fill="#f07840" stroke="#a04410" stroke-width="1.5"/>
      <circle class="fruit" id="tf8"  cx="213" cy="174" r="8"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf9"  cx="133" cy="190" r="9"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      <circle class="fruit" id="tf10" cx="192" cy="188" r="8"  fill="#f07840" stroke="#a04410" stroke-width="1.5"/>
      <circle class="fruit" id="tf11" cx="158" cy="195" r="9"  fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
    </g>

    <!-- ══ TRUCK ══ (right side) -->
    <g id="truck" transform="translate(600,260)">
      <ellipse cx="105" cy="76" rx="98" ry="11" fill="#000" opacity="0.22"/>
      <!-- Bed -->
      <rect x="42" y="8" width="168" height="55" rx="4" fill="#d44f28" stroke="#8b2e10" stroke-width="1.5"/>
      <line x1="130" y1="8"  x2="130" y2="63" stroke="#8b2e10" stroke-width="1.5"/>
      <line x1="42"  y1="34" x2="210" y2="34" stroke="#8b2e10" stroke-width="1.2" opacity="0.6"/>
      <!-- Cab -->
      <rect x="0" y="18" width="50" height="45" rx="6" fill="#b03518" stroke="#7a1e06" stroke-width="1.5"/>
      <rect x="5" y="22" width="30" height="22" rx="3" fill="#3a6a88" opacity="0.85" stroke="#5a9ab8" stroke-width="1"/>
      <rect x="38" y="28" width="10" height="10" rx="1" fill="#7a1e06"/>
      <!-- Wheels -->
      <circle cx="22"  cy="68" r="13" fill="#1a1a1a" stroke="#444" stroke-width="2"/>
      <circle cx="22"  cy="68" r="5"  fill="#333"/>
      <circle cx="78"  cy="68" r="13" fill="#1a1a1a" stroke="#444" stroke-width="2"/>
      <circle cx="78"  cy="68" r="5"  fill="#333"/>
      <circle cx="150" cy="68" r="13" fill="#1a1a1a" stroke="#444" stroke-width="2"/>
      <circle cx="150" cy="68" r="5"  fill="#333"/>
      <circle cx="190" cy="68" r="13" fill="#1a1a1a" stroke="#444" stroke-width="2"/>
      <circle cx="190" cy="68" r="5"  fill="#333"/>
      <!-- Headlight -->
      <circle cx="2"   cy="42" r="6" fill="#fffde8" opacity="0.88" filter="url(#softGlow)"/>
      <text x="126" y="44" text-anchor="middle" font-size="10" fill="rgba(255,255,255,0.45)" font-family="DM Mono,monospace" font-weight="400">FRESH CO.</text>
    </g>

    <!-- ══ CAL GROUP (crate + loader, slides together) ══ -->
    <g id="cal" style="transform:translate(0,0)">

      <!-- Crate at SVG 395,288 -->
      <g id="crate-group" transform="translate(395,288)">
        <ellipse cx="42" cy="48" rx="46" ry="9" fill="#000" opacity="0.2"/>
        <!-- Wood body -->
        <rect x="0" y="0" width="84" height="46" rx="5" fill="#c8924e" stroke="#7a4a10" stroke-width="1.5"/>
        <!-- Planks -->
        <line x1="28" y1="0"  x2="28" y2="46" stroke="#7a4a10" stroke-width="1.5"/>
        <line x1="56" y1="0"  x2="56" y2="46" stroke="#7a4a10" stroke-width="1.5"/>
        <line x1="0"  y1="15" x2="84" y2="15" stroke="#7a4a10" stroke-width="1.2" opacity="0.7"/>
        <line x1="0"  y1="31" x2="84" y2="31" stroke="#7a4a10" stroke-width="1.2" opacity="0.7"/>
        <!-- Shine -->
        <rect x="2" y="2" width="80" height="42" rx="4" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
        <!-- Label -->
        <text x="42" y="-8" text-anchor="middle" font-size="11" fill="#a87030" font-family="DM Mono,monospace" font-weight="400" letter-spacing="0.08em">CRATE</text>
        <!-- Fruit slots (3 rows × 4 cols = 12) -->
        <g id="crate-slots">
          <circle id="cs0"  cx="10" cy="9"  r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs1"  cx="28" cy="9"  r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs2"  cx="56" cy="9"  r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs3"  cx="74" cy="9"  r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs4"  cx="10" cy="23" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs5"  cx="28" cy="23" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs6"  cx="56" cy="23" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs7"  cx="74" cy="23" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs8"  cx="10" cy="37" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs9"  cx="28" cy="37" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs10" cx="56" cy="37" r="5.5" fill="rgba(0,0,0,0.15)"/>
          <circle id="cs11" cx="74" cy="37" r="5.5" fill="rgba(0,0,0,0.15)"/>
        </g>
      </g>

      <!-- Loader at SVG x=500, y=270 (right of crate) -->
      <g id="loader-char" transform="translate(500,270)">
        <!-- Zzz -->
        <g id="loader-zzz" opacity="1">
          <text class="zzz" x="14" y="-4"  font-size="10" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
          <text class="zzz" x="20" y="-13" font-size="12" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
          <text class="zzz" x="27" y="-24" font-size="14" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">Z</text>
        </g>
        <!-- Sleep halo -->
        <circle id="loader-halo" cx="0" cy="6" r="18" fill="rgba(136,160,255,0.08)" stroke="rgba(136,160,255,0.25)" stroke-width="1.2" opacity="1"/>
        <!-- Shadow -->
        <ellipse cx="0" cy="52" rx="15" ry="5" fill="#000" opacity="0.18"/>
        <!-- Body -->
        <rect x="-11" y="21" width="22" height="27" rx="4" fill="#e84060" id="loader-body"/>
        <!-- Head -->
        <circle cx="0" cy="12" r="12" fill="#f5cba7" stroke="#c8956e" stroke-width="1"/>
        <!-- Hat -->
        <rect x="-13" y="3"  width="26" height="6"  rx="2" fill="#a02030"/>
        <rect x="-8"  y="-4" width="16" height="10" rx="2" fill="#a02030"/>
        <!-- Eyes -->
        <circle cx="-4" cy="14" r="2.2" fill="#333"/>
        <circle cx="4"  cy="14" r="2.2" fill="#333"/>
        <!-- Arms -->
        <rect id="loader-arm-l" x="-24" y="23" width="14" height="7" rx="3.5" fill="#e84060"/>
        <rect id="loader-arm-r" x="10"  y="23" width="14" height="7" rx="3.5" fill="#e84060"/>
        <!-- Legs -->
        <rect x="-9" y="46" width="8" height="14" rx="3" fill="#701020"/>
        <rect x="2"  y="46" width="8" height="14" rx="3" fill="#701020"/>
        <!-- Label -->
        <text x="0" y="72" text-anchor="middle" font-size="10" fill="#e84060" font-family="DM Mono,monospace" letter-spacing="0.05em">LOADER</text>
      </g>
    </g>

    <!-- ══ PICKER 0 (uid=0) – cyan ══ -->
    <g id="picker-0" style="transform:translate(320px,270px)">
      <g id="p0-zzz" opacity="0">
        <text class="zzz" x="14" y="-4"  font-size="9"  fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
        <text class="zzz" x="19" y="-12" font-size="11" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
        <text class="zzz" x="25" y="-22" font-size="13" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">Z</text>
      </g>
      <circle id="p0-halo" cx="0" cy="6" r="18" fill="rgba(136,160,255,0.08)" stroke="rgba(136,160,255,0.25)" stroke-width="1.2" opacity="0"/>
      <ellipse cx="0" cy="52" rx="14" ry="5" fill="#000" opacity="0.18"/>
      <rect x="-10" y="21" width="20" height="26" rx="4" fill="#4cc9f0" id="p0-body"/>
      <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#c8956e" stroke-width="1"/>
      <rect x="-12" y="3"  width="24" height="6"  rx="2" fill="#1a7a9a"/>
      <rect x="-7"  y="-4" width="14" height="10" rx="2" fill="#1a7a9a"/>
      <circle cx="-4" cy="13" r="2" fill="#333"/>
      <circle cx="4"  cy="13" r="2" fill="#333"/>
      <rect x="-22" y="23" width="13" height="6" rx="3" fill="#4cc9f0"/>
      <rect x="9"   y="23" width="13" height="6" rx="3" fill="#4cc9f0"/>
      <!-- Carried fruit -->
      <g id="p0-carry" opacity="0">
        <circle cx="18" cy="20" r="7.5" fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      </g>
      <rect x="-9" y="45" width="8" height="13" rx="3" fill="#1a6080"/>
      <rect x="2"  y="45" width="8" height="13" rx="3" fill="#1a6080"/>
      <text x="0" y="72" text-anchor="middle" font-size="10" fill="#4cc9f0" font-family="DM Mono,monospace">P1</text>
    </g>

    <!-- ══ PICKER 1 (uid=1) – orange ══ -->
    <g id="picker-1" style="transform:translate(348px,270px)">
      <g id="p1-zzz" opacity="0">
        <text class="zzz" x="14" y="-4"  font-size="9"  fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
        <text class="zzz" x="19" y="-12" font-size="11" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
        <text class="zzz" x="25" y="-22" font-size="13" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">Z</text>
      </g>
      <circle id="p1-halo" cx="0" cy="6" r="18" fill="rgba(136,160,255,0.08)" stroke="rgba(136,160,255,0.25)" stroke-width="1.2" opacity="0"/>
      <ellipse cx="0" cy="52" rx="14" ry="5" fill="#000" opacity="0.18"/>
      <rect x="-10" y="21" width="20" height="26" rx="4" fill="#f77f2a" id="p1-body"/>
      <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#c8956e" stroke-width="1"/>
      <rect x="-12" y="3"  width="24" height="6"  rx="2" fill="#903808"/>
      <rect x="-7"  y="-4" width="14" height="10" rx="2" fill="#903808"/>
      <circle cx="-4" cy="13" r="2" fill="#333"/>
      <circle cx="4"  cy="13" r="2" fill="#333"/>
      <rect x="-22" y="23" width="13" height="6" rx="3" fill="#f77f2a"/>
      <rect x="9"   y="23" width="13" height="6" rx="3" fill="#f77f2a"/>
      <g id="p1-carry" opacity="0">
        <circle cx="18" cy="20" r="7.5" fill="#f07840" stroke="#a04410" stroke-width="1.5"/>
      </g>
      <rect x="-9" y="45" width="8" height="13" rx="3" fill="#702808"/>
      <rect x="2"  y="45" width="8" height="13" rx="3" fill="#702808"/>
      <text x="0" y="72" text-anchor="middle" font-size="10" fill="#f77f2a" font-family="DM Mono,monospace">P2</text>
    </g>

    <!-- ══ PICKER 2 (uid=2) – purple ══ -->
    <g id="picker-2" style="transform:translate(376px,270px)">
      <g id="p2-zzz" opacity="0">
        <text class="zzz" x="14" y="-4"  font-size="9"  fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
        <text class="zzz" x="19" y="-12" font-size="11" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">z</text>
        <text class="zzz" x="25" y="-22" font-size="13" fill="rgba(170,196,255,0.9)" font-family="DM Mono,monospace">Z</text>
      </g>
      <circle id="p2-halo" cx="0" cy="6" r="18" fill="rgba(136,160,255,0.08)" stroke="rgba(136,160,255,0.25)" stroke-width="1.2" opacity="0"/>
      <ellipse cx="0" cy="52" rx="14" ry="5" fill="#000" opacity="0.18"/>
      <rect x="-10" y="21" width="20" height="26" rx="4" fill="#b07ef0" id="p2-body"/>
      <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#c8956e" stroke-width="1"/>
      <rect x="-12" y="3"  width="24" height="6"  rx="2" fill="#5c1ea0"/>
      <rect x="-7"  y="-4" width="14" height="10" rx="2" fill="#5c1ea0"/>
      <circle cx="-4" cy="13" r="2" fill="#333"/>
      <circle cx="4"  cy="13" r="2" fill="#333"/>
      <rect x="-22" y="23" width="13" height="6" rx="3" fill="#b07ef0"/>
      <rect x="9"   y="23" width="13" height="6" rx="3" fill="#b07ef0"/>
      <g id="p2-carry" opacity="0">
        <circle cx="18" cy="20" r="7.5" fill="#e8373e" stroke="#a02020" stroke-width="1.5"/>
      </g>
      <rect x="-9" y="45" width="8" height="13" rx="3" fill="#3a0878"/>
      <rect x="2"  y="45" width="8" height="13" rx="3" fill="#3a0878"/>
      <text x="0" y="72" text-anchor="middle" font-size="10" fill="#b07ef0" font-family="DM Mono,monospace">P2</text>
    </g>

    <!-- Fireflies -->
    <g id="fireflies" opacity="0.7">
      <circle cx="260" cy="280" r="2.5" fill="#ccff80" filter="url(#softGlow)" opacity="0.6"/>
      <circle cx="290" cy="310" r="2"   fill="#ccff80" filter="url(#softGlow)" opacity="0.5"/>
      <circle cx="240" cy="295" r="2.5" fill="#ccff80" filter="url(#softGlow)" opacity="0.7"/>
    </g>

    </svg>
    </div>

    <!-- Thread badges row -->
    <div class="badges-row" id="badges-row">
      <div class="tbadge sleeping" id="badge-p0"><div class="dot"></div><span>P1 💤</span></div>
      <div class="tbadge sleeping" id="badge-p1"><div class="dot"></div><span>P2 💤</span></div>
      <div class="tbadge sleeping" id="badge-p2"><div class="dot"></div><span>P3 💤</span></div>
      <div class="tbadge sleeping" id="badge-loader"><div class="dot"></div><span>Loader 💤</span></div>
    </div>

  </div><!-- /scene-col -->

  <div class="side-col">
    <div class="side-section">
      <div class="side-label">Stats</div>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-val" id="s-picked">0</div>
          <div class="stat-lbl">Fruits picked</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="s-crate">0/12</div>
          <div class="stat-lbl">Crate filled</div>
        </div>
      </div>
    </div>
    <div class="side-section">
      <div class="side-label">Total progress</div>
      <div class="prog-bar"><div class="prog-fill" id="prog-fill"></div></div>
      <div class="prog-nums"><span id="s-pct">0%</span><span id="s-total">0 / ?</span></div>
    </div>
    <div class="log-wrap">
      <h3>Event log</h3>
      <div id="log-entries"></div>
    </div>
  </div>

</main>

<script>
// ────────────────────────────────────────────────────────────────────────────
// LAYOUT CONSTANTS  (SVG coords)
// ────────────────────────────────────────────────────────────────────────────
// Each picker's resting home position (SVG coords for transform translate)
const HOME = [
  [320, 270],   // picker-0
  [348, 270],   // picker-1
  [376, 270],   // picker-2
];
// Where each picker walks when going to the tree (staggered x so they don't overlap)
const TREE_DEST = [
  [148, 270],
  [164, 270],
  [180, 270],
];
// Where each picker walks to drop fruit (near crate left edge)
const CRATE_DEST = [
  [352, 270],
  [365, 270],
  [378, 270],
];

const WALK_MS   = 700;
const RETURN_MS = 550;
const CAL_SLIDE_DX = 162; // crate+loader slide this many px right to reach truck

// ────────────────────────────────────────────────────────────────────────────
// STATE
// ────────────────────────────────────────────────────────────────────────────
let totalFruits = 20;
let fruitsPicked = 0;
let crateCount = 0;
let treeIndex = 0; // which tree fruit to pop next

// Per-picker state: tracks what state each picker thread is in so we can
// animate correctly even when multiple pickers are in-flight simultaneously.
// States: 'idle' | 'walking-to-tree' | 'at-tree' | 'walking-to-crate' | 'at-crate' | 'sleeping' | 'waiting' | 'done'
const pickerState = ['idle', 'idle', 'idle'];

// ────────────────────────────────────────────────────────────────────────────
// HELPERS
// ────────────────────────────────────────────────────────────────────────────
function setPx(el, x, y, ms, ease) {
  el.style.transition = ms ? `transform ${ms}ms ${ease || 'cubic-bezier(0.4,0,0.2,1)'}` : 'none';
  el.style.transform  = `translate(${x}px,${y}px)`;
}

function movePicker(uid, x, y, ms) {
  const el = document.getElementById('picker-' + uid);
  if (el) setPx(el, x, y, ms);
}

function setOpacity(id, v, ms) {
  const el = document.getElementById(id);
  if (!el) return;
  if (ms) el.style.transition = `opacity ${ms}ms`;
  el.setAttribute('opacity', v);
}

function setSleep(id, on) {
  // id = 'loader' or picker uid (0,1,2)
  const prefix = id === 'loader' ? 'loader' : 'p' + id;
  setOpacity(prefix + '-zzz',  on ? 1 : 0, 350);
  setOpacity(prefix + '-halo', on ? 1 : 0, 350);
  const body = document.getElementById(prefix + '-body');
  if (body) { body.style.transition = 'opacity 0.35s'; body.setAttribute('opacity', on ? '0.45' : '1'); }
}

function setCarry(uid, on) {
  const el = document.getElementById('p' + uid + '-carry');
  if (el) { el.style.transition = 'opacity 0.2s'; el.setAttribute('opacity', on ? '1' : '0'); }
}

function badge(id, state, text) {
  const el = document.getElementById('badge-' + id);
  if (!el) return;
  el.className = 'tbadge ' + state;
  el.querySelector('span').textContent = text;
}

function fillSlot(slot) {
  const el = document.getElementById('cs' + slot);
  if (!el) return;
  el.setAttribute('fill', '#e8373e');
  el.setAttribute('r', '6.5');
}

function clearSlots() {
  for (let i = 0; i < 12; i++) {
    const el = document.getElementById('cs' + i);
    if (el) { el.setAttribute('fill', 'rgba(0,0,0,0.15)'); el.setAttribute('r', '5.5'); }
  }
}

function popTreeFruit() {
  const fi = treeIndex++;
  const el = document.getElementById('tf' + fi);
  if (!el) return;
  el.style.transition = 'r 0.18s ease, opacity 0.35s ease';
  el.setAttribute('r', '15');
  setTimeout(() => { el.setAttribute('r', '0'); el.setAttribute('opacity', '0'); }, 160);
  setTimeout(() => el.remove(), 550);
}

function shakeCrate() {
  const g = document.getElementById('crate-group');
  if (!g) return;
  const base = 'translate(395,288)';
  const seq = [base+' rotate(-1.5)', base+' translate(3,0) rotate(1)', base+' translate(-2,0)', base+' translate(2,0)', base];
  seq.forEach((s,i) => setTimeout(() => g.setAttribute('transform', s), i * 60));
  setTimeout(() => g.setAttribute('transform', base), seq.length * 60 + 40);
}

// ────────────────────────────────────────────────────────────────────────────
// CRATE + LOADER SLIDE
// ────────────────────────────────────────────────────────────────────────────
const calEl = document.getElementById('cal');
function calSlide(dx, ms) {
  calEl.style.transition = `transform ${ms}ms cubic-bezier(0.4,0,0.2,1)`;
  calEl.style.transform  = `translate(${dx}px,0)`;
}

function setLoaderArms(up) {
  const al = document.getElementById('loader-arm-l');
  const ar = document.getElementById('loader-arm-r');
  if (al) { al.style.transition = 'y 0.3s'; al.setAttribute('y', up ? '10' : '23'); }
  if (ar) { ar.style.transition = 'y 0.3s'; ar.setAttribute('y', up ? '10' : '23'); }
}

// ────────────────────────────────────────────────────────────────────────────
// TRUCK ANIMATION
// ────────────────────────────────────────────────────────────────────────────
function animateTruck() {
  const t = document.getElementById('truck');
  if (!t) return;
  // Drive away right
  t.style.transition = 'transform 1.4s cubic-bezier(0.4,0,0.8,1)';
  t.style.transform  = 'translate(340px,0)';
  setTimeout(() => {
    // Teleport left
    t.style.transition = 'none';
    t.style.transform  = 'translate(-380px,0)';
    requestAnimationFrame(() => requestAnimationFrame(() => {
      // Drive back in
      t.style.transition = 'transform 1.2s cubic-bezier(0.2,0,0.4,1)';
      t.style.transform  = 'translate(0,0)';
    }));
  }, 1600);
}

// ────────────────────────────────────────────────────────────────────────────
// STATS + LOG
// ────────────────────────────────────────────────────────────────────────────
function updateStats() {
  document.getElementById('s-picked').textContent = fruitsPicked;
  document.getElementById('s-crate').textContent  = crateCount + '/12';
  const pct = totalFruits > 0 ? Math.round(fruitsPicked / totalFruits * 100) : 0;
  document.getElementById('s-pct').textContent   = pct + '%';
  document.getElementById('s-total').textContent = fruitsPicked + ' / ' + totalFruits;
  document.getElementById('prog-fill').style.width = pct + '%';
}

function addLog(actor, uid, event) {
  const panel = document.getElementById('log-entries');
  const d     = document.createElement('div');
  d.className = 'log-entry';
  let tagClass, label;
  if (actor === 'LOADER') { tagClass = 'lt-loader'; label = 'LOADER'; }
  else { tagClass = 'lt-p' + uid; label = 'P' + (uid + 1); }
  const evName = event.replace('EventType.','').replace(/_/g,' ');
  d.innerHTML = `<span class="log-tag ${tagClass}">${label}</span><span>${evName}</span>`;
  panel.prepend(d);
  while (panel.children.length > 80) panel.removeChild(panel.lastChild);
}

// ────────────────────────────────────────────────────────────────────────────
// EVENT HANDLERS — each fires the correct animation for one specific picker
// ────────────────────────────────────────────────────────────────────────────

function onPickerCheckSlot(uid) {
  setSleep(uid, false);
  badge('p'+uid, 'active', `P${uid+1} → 🌳`);
  pickerState[uid] = 'walking-to-tree';
  movePicker(uid, TREE_DEST[uid][0], TREE_DEST[uid][1], WALK_MS);
}

function onPickerPickAndAdd(uid, slot) {
  // Pop a fruit off the tree, picker walks to crate
  pickerState[uid] = 'at-tree';
  popTreeFruit();
  setCarry(uid, true);
  badge('p'+uid, 'active', `P${uid+1} ← 🍎`);

  setTimeout(() => {
    pickerState[uid] = 'walking-to-crate';
    movePicker(uid, CRATE_DEST[uid][0], CRATE_DEST[uid][1], WALK_MS);

    setTimeout(() => {
      // Drop fruit
      pickerState[uid] = 'at-crate';
      setCarry(uid, false);
      fillSlot(slot);
      shakeCrate();
      badge('p'+uid, 'active', `P${uid+1} dropping`);

      // Walk home
      setTimeout(() => {
        pickerState[uid] = 'idle';
        movePicker(uid, HOME[uid][0], HOME[uid][1], RETURN_MS);
        setTimeout(() => {
          if (fruitsPicked >= totalFruits) {
            badge('p'+uid, 'done', `P${uid+1} done`);
          } else {
            setSleep(uid, true);
            badge('p'+uid, 'sleeping', `P${uid+1} 💤`);
            pickerState[uid] = 'sleeping';
          }
        }, RETURN_MS + 150);
      }, 300);
    }, WALK_MS + 50);
  }, WALK_MS * 0.5); // start walking after half the tree-walk
}

function onPickerWaitForSlot(uid) {
  // Crate is full — picker waits
  badge('p'+uid, 'waiting', `P${uid+1} ⏳`);
  pickerState[uid] = 'waiting';
  movePicker(uid, HOME[uid][0], HOME[uid][1], RETURN_MS);
}

function onLoaderStartLoad() {
  setSleep('loader', false);
  setLoaderArms(true);
  badge('loader', 'active', 'Loader → 🚛');
  calSlide(CAL_SLIDE_DX, 1100);
  setTimeout(animateTruck, 300);
}

function onLoaderEmptyCrate() {
  calSlide(0, 950);
  setLoaderArms(false);
  clearSlots();
  crateCount = 0;

  setTimeout(() => {
    if (fruitsPicked >= totalFruits) {
      badge('loader', 'done', 'Loader done');
      setSleep('loader', false);
    } else {
      setSleep('loader', true);
      badge('loader', 'sleeping', 'Loader 💤');
    }
    // Wake waiting pickers
    for (let i = 0; i < 3; i++) {
      if (pickerState[i] === 'waiting' && fruitsPicked < totalFruits) {
        setSleep(i, false);
        badge('p'+i, 'active', `P${i+1} ready`);
        pickerState[i] = 'idle';
      }
    }
  }, 980);
}

// ────────────────────────────────────────────────────────────────────────────
// POLL LOOP — drain /state every 200ms, process each event in order
// ────────────────────────────────────────────────────────────────────────────
const pill = document.getElementById('pill');

async function poll() {
  try {
    const res = await fetch('/state');
    if (res.ok) {
      const events = await res.json();
      for (const ev of events) {
        const actor = ev.actor;
        // uid is the picker index (0,1,2). For LOADER it's null.
        const uid   = (ev.uid !== null && ev.uid !== undefined) ? Number(ev.uid) : null;
        const event = ev.event || '';

        // Update global state from server truth
        totalFruits  = ev.total_fruits  || totalFruits;
        fruitsPicked = ev.fruits_picked || 0;

        // Sync crate count from the crate array
        if (ev.crate) crateCount = ev.crate.filter(v => v === 1).length;

        addLog(actor, uid, event);
        updateStats();
        pill.textContent = 'Running…'; pill.className = 'running';

        if (actor === 'PICKER') {
          if (event.includes('check_for_a_slot'))        onPickerCheckSlot(uid);
          if (event.includes('pick_fruit_and_add_to_crate')) onPickerPickAndAdd(uid, ev.crate_slot_number);
          if (event.includes('wait_for_a_slot'))         onPickerWaitForSlot(uid);
        } else if (actor === 'LOADER') {
          if (event.includes('start_truck_load')) onLoaderStartLoad();
          if (event.includes('empty_crate'))      onLoaderEmptyCrate();
        }

        // Check completion
        if (fruitsPicked >= totalFruits && crateCount === 0 && fruitsPicked > 0) {
          pill.textContent = 'Done! 🎉'; pill.className = 'done';
        }
      }
    }
  } catch(e) { /* server not ready */ }
  setTimeout(poll, 200);
}

// Init
setSleep(0, true); setSleep(1, true); setSleep(2, true); setSleep('loader', true);
updateStats();
poll();
</script>
</body>
</html>
"""

# Thread-safe event queue (deque for fast popleft)
_event_queue = deque()

@app.route('/update', methods=['POST'])
def update_state():
    data = request.json
    _event_queue.append(data)
    actor = data.get('actor','?')
    uid   = data.get('uid', '-')
    event = data.get('event','?')
    slot  = data.get('crate_slot_number')
    total = data.get('fruits_picked', 0)
    print(f"[{actor}{'#'+str(uid) if uid is not None else ''}] {event} | slot={slot} | picked={total}")
    return jsonify({"status": "ok"}), 200

@app.route('/state', methods=['GET'])
def get_state():
    """Drain the queue and return all pending events as a JSON array."""
    events = []
    while _event_queue:
        events.append(_event_queue.popleft())
    return jsonify(events)

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(port=5000, debug=False)