from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# NOTE: For per-picker sleep indicators, pass uid in send_action on the client:
#   state = { "actor": actor, "uid": uid, "event": ..., ... }
# The server works fine without it (falls back to round-robin assignment).

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Orchard Simulation</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0a0a0f;
  color: #e8e4d8;
  font-family: 'DM Sans', sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
}

header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.2rem 2.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
header h1 {
  font-family: 'Playfair Display', serif;
  font-size: 1.5rem; color: #e8c87a; letter-spacing: 0.02em;
}
#status-pill {
  font-size: 12px; font-weight: 500; padding: 4px 14px; border-radius: 20px;
  background: rgba(74,124,63,0.2); border: 1px solid rgba(74,124,63,0.5); color: #7ecb72;
  transition: all 0.4s;
}
#status-pill.loading { background: rgba(230,121,81,0.2); border-color: rgba(230,121,81,0.5); color: #f4a87a; }
#status-pill.done    { background: rgba(76,201,240,0.2);  border-color: rgba(76,201,240,0.5);  color: #9de3f5; }

.scene-wrapper { padding: 2rem 2.5rem 0; }
#scene {
  width: 100%; border-radius: 16px; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.07);
  background: #c9e8f7; position: relative;
}
#main-svg { display: block; width: 100%; }

/* Sleep zzz */
@keyframes zzzFloat {
  0%   { transform: translateY(0) scale(1);    opacity: 1; }
  100% { transform: translateY(-18px) scale(0.6); opacity: 0; }
}
.zzz-letter {
  animation: zzzFloat 1.4s ease-in-out infinite;
}
.zzz-letter:nth-child(2) { animation-delay: 0.35s; }
.zzz-letter:nth-child(3) { animation-delay: 0.7s; }

/* Log */
.bottom-grid {
  display: grid; grid-template-columns: 1fr 340px;
  gap: 1.5rem; padding: 1.5rem 2.5rem 2rem;
}
#log-panel {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px; padding: 1rem 1.25rem;
  max-height: 220px; overflow-y: auto;
  scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.15) transparent;
}
#log-panel h3 {
  font-size: 11px; font-weight: 500; text-transform: uppercase;
  letter-spacing: 0.1em; color: rgba(255,255,255,0.3); margin-bottom: 0.75rem;
}
.log-entry {
  font-size: 13px; line-height: 1.6; color: rgba(232,228,216,0.7);
  padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
  display: flex; gap: 8px; align-items: baseline;
}
.log-entry .tag {
  font-size: 10px; font-weight: 500; padding: 1px 6px;
  border-radius: 4px; flex-shrink: 0;
}
.tag-picker0 { background: rgba(76,201,240,0.15);  color: #4cc9f0; }
.tag-picker1 { background: rgba(247,127,0,0.15);   color: #f77f00; }
.tag-picker2 { background: rgba(155,93,229,0.15);  color: #9b5de5; }
.tag-loader  { background: rgba(230,57,70,0.15);   color: #e63946; }

.stats-panel { display: flex; flex-direction: column; gap: 1rem; }
.stat-card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px; padding: 0.9rem 1.25rem;
  display: flex; align-items: center; justify-content: space-between;
}
.stat-label { font-size: 12px; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.08em; }
.stat-value { font-size: 22px; font-weight: 500; font-variant-numeric: tabular-nums; color: #e8e4d8; }

.progress-wrap {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px; padding: 0.9rem 1.25rem;
}
.progress-label {
  display: flex; justify-content: space-between; font-size: 12px;
  color: rgba(255,255,255,0.35); margin-bottom: 8px;
  text-transform: uppercase; letter-spacing: 0.08em;
}
.progress-bar { height: 6px; background: rgba(255,255,255,0.07); border-radius: 3px; overflow: hidden; }
.progress-fill {
  height: 100%; background: linear-gradient(90deg,#4cc9f0,#9b5de5);
  border-radius: 3px; transition: width 0.5s ease; width: 0%;
}

/* Thread badges */
.thread-badges {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px; padding: 0.9rem 1.25rem;
}
.thread-badges-label {
  font-size: 11px; font-weight: 500; text-transform: uppercase;
  letter-spacing: 0.1em; color: rgba(255,255,255,0.3); margin-bottom: 10px;
}
.badges-row { display: flex; gap: 8px; flex-wrap: wrap; }
.tbadge {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 10px; border-radius: 8px; font-size: 12px; font-weight: 500;
  border: 1px solid; transition: all 0.35s;
}
.tbadge .dot { width: 7px; height: 7px; border-radius: 50%; transition: background 0.3s; }
.tbadge.active   { background: rgba(100,220,100,0.08); border-color: rgba(100,220,100,0.35); }
.tbadge.sleeping { background: rgba(120,150,255,0.08); border-color: rgba(120,150,255,0.35); }
.tbadge.waiting  { background: rgba(255,200,60,0.08);  border-color: rgba(255,200,60,0.35); }
.tbadge.done     { background: rgba(100,100,100,0.08); border-color: rgba(100,100,100,0.35); }
.tbadge.active   .dot { background: #6ddc6d; }
.tbadge.sleeping .dot { background: #8899ff; box-shadow: 0 0 5px #8899ff88; }
.tbadge.waiting  .dot { background: #ffc83c; }
.tbadge.done     .dot { background: #666; }
.tbadge.active   span { color: #8ef08e; }
.tbadge.sleeping span { color: #aac4ff; }
.tbadge.waiting  span { color: #ffd97a; }
.tbadge.done     span { color: #777; }
</style>
</head>
<body>

<header>
  <h1>🍎 Orchard Simulation</h1>
  <div id="status-pill">Waiting…</div>
</header>

<div class="scene-wrapper">
<div id="scene">
<svg id="main-svg" viewBox="0 0 900 430" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#b8d8f0"/>
    <stop offset="100%" stop-color="#deeef8"/>
  </linearGradient>
  <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#5a8c50"/>
    <stop offset="60%"  stop-color="#4a7a40"/>
    <stop offset="100%" stop-color="#3a6030"/>
  </linearGradient>
  <linearGradient id="trunkGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#5a2e0f"/>
    <stop offset="50%"  stop-color="#7a4020"/>
    <stop offset="100%" stop-color="#5a2e0f"/>
  </linearGradient>
  <linearGradient id="leafGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#4a9e44"/>
    <stop offset="100%" stop-color="#2e6b28"/>
  </linearGradient>
</defs>

<!-- Sky -->
<rect width="900" height="430" fill="url(#skyGrad)"/>

<!-- Clouds -->
<g opacity="0.65">
  <ellipse cx="120" cy="60" rx="55" ry="22" fill="white"/>
  <ellipse cx="155" cy="48" rx="38" ry="26" fill="white"/>
  <ellipse cx="90"  cy="55" rx="30" ry="18" fill="white"/>
</g>
<g opacity="0.5">
  <ellipse cx="700" cy="52" rx="45" ry="18" fill="white"/>
  <ellipse cx="730" cy="42" rx="32" ry="22" fill="white"/>
  <ellipse cx="675" cy="48" rx="28" ry="15" fill="white"/>
</g>

<!-- Ground -->
<rect x="0" y="315" width="900" height="115" fill="url(#groundGrad)"/>
<line x1="0" y1="318" x2="900" y2="318" stroke="#3a6030" stroke-width="1" opacity="0.5"/>

<!-- Dirt path from tree zone to crate zone -->
<ellipse cx="370" cy="330" rx="195" ry="9" fill="#9a7840" opacity="0.22"/>

<!-- === TREE === -->
<g id="tree" transform="translate(150,0)">
  <ellipse cx="0" cy="318" rx="55" ry="12" fill="#00000020"/>
  <path d="M-14,315 C-16,260 -10,200 0,182 C10,200 16,260 14,315 Z" fill="url(#trunkGrad)"/>
  <path d="M0,225 Q-40,195 -65,172" stroke="#5a2e0f" stroke-width="8" fill="none" stroke-linecap="round"/>
  <path d="M0,225 Q40,195  65,172" stroke="#5a2e0f" stroke-width="8" fill="none" stroke-linecap="round"/>
  <path d="M0,205 Q-15,168 -10,142" stroke="#5a2e0f" stroke-width="6" fill="none" stroke-linecap="round"/>
  <ellipse cx="0"   cy="157" rx="70" ry="60" fill="url(#leafGrad)"/>
  <ellipse cx="-60" cy="172" rx="50" ry="42" fill="#3e8e38"/>
  <ellipse cx="60"  cy="170" rx="50" ry="42" fill="#3e8e38"/>
  <ellipse cx="-20" cy="117" rx="42" ry="35" fill="#4aaa44"/>
  <ellipse cx="20"  cy="117" rx="42" ry="35" fill="#4aaa44"/>
  <ellipse cx="0"   cy="107" rx="35" ry="30" fill="#55c04e"/>
  <ellipse cx="-30" cy="127" rx="20" ry="12" fill="#62cc5a" opacity="0.45"/>
  <ellipse cx="25"  cy="122" rx="18" ry="11" fill="#62cc5a" opacity="0.38"/>
</g>

<!-- Fruits on tree (12) -->
<g id="fruits">
  <circle class="fruit" id="f0"  cx="140" cy="142" r="9"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f1"  cx="163" cy="127" r="8"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f2"  cx="185" cy="137" r="9"  fill="#f4845f" stroke="#d06040" stroke-width="1.5"/>
  <circle class="fruit" id="f3"  cx="120" cy="162" r="8"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f4"  cx="195" cy="157" r="8"  fill="#f4845f" stroke="#d06040" stroke-width="1.5"/>
  <circle class="fruit" id="f5"  cx="150" cy="172" r="9"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f6"  cx="170" cy="167" r="8"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f7"  cx="105" cy="177" r="9"  fill="#f4845f" stroke="#d06040" stroke-width="1.5"/>
  <circle class="fruit" id="f8"  cx="210" cy="172" r="8"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f9"  cx="135" cy="187" r="9"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
  <circle class="fruit" id="f10" cx="190" cy="187" r="8"  fill="#f4845f" stroke="#d06040" stroke-width="1.5"/>
  <circle class="fruit" id="f11" cx="160" cy="192" r="9"  fill="#e63946" stroke="#c0303a" stroke-width="1.5"/>
</g>

<!-- === TRUCK === -->
<g id="truck" transform="translate(585,252)">
  <ellipse cx="100" cy="73" rx="92" ry="10" fill="#00000022"/>
  <rect x="40"  y="10" width="165" height="52" rx="4" fill="#e76f51" stroke="#c1440e" stroke-width="1.5"/>
  <line x1="130" y1="10" x2="130" y2="62" stroke="#c1440e" stroke-width="1.5"/>
  <line x1="40"  y1="36" x2="205" y2="36" stroke="#c1440e" stroke-width="1.5"/>
  <rect x="0"   y="20" width="48"  height="42" rx="5" fill="#c1440e" stroke="#9a3510" stroke-width="1.5"/>
  <rect x="5"   y="24" width="30"  height="20" rx="3" fill="#7ac8e6" opacity="0.8" stroke="#aaddee" stroke-width="1"/>
  <rect x="38"  y="25" width="8"   height="8"  rx="1" fill="#9a3510"/>
  <circle cx="20"  cy="66" r="12" fill="#2c2c2c" stroke="#555" stroke-width="2"/>
  <circle cx="20"  cy="66" r="5"  fill="#444"/>
  <circle cx="75"  cy="66" r="12" fill="#2c2c2c" stroke="#555" stroke-width="2"/>
  <circle cx="75"  cy="66" r="5"  fill="#444"/>
  <circle cx="145" cy="66" r="12" fill="#2c2c2c" stroke="#555" stroke-width="2"/>
  <circle cx="145" cy="66" r="5"  fill="#444"/>
  <circle cx="185" cy="66" r="12" fill="#2c2c2c" stroke="#555" stroke-width="2"/>
  <circle cx="185" cy="66" r="5"  fill="#444"/>
  <text x="122" y="43" text-anchor="middle" font-size="10" fill="rgba(255,255,255,0.6)" font-family="DM Sans,sans-serif" font-weight="500">FRESH CO.</text>
</g>

<!-- === CRATE-AND-LOADER GROUP (slides together during unload) === -->
<g id="cal">
  <!-- Crate at absolute SVG 378,283 within this group (group origin = 0,0) -->
  <g id="crate-group" transform="translate(378,283)">
    <ellipse cx="40" cy="46" rx="44" ry="8" fill="#00000018"/>
    <rect x="0" y="0" width="80" height="44" rx="4" fill="#c8a96e" stroke="#8B6914" stroke-width="1.5"/>
    <line x1="26" y1="0"  x2="26" y2="44" stroke="#8B6914" stroke-width="1.5"/>
    <line x1="54" y1="0"  x2="54" y2="44" stroke="#8B6914" stroke-width="1.5"/>
    <line x1="0"  y1="14" x2="80" y2="14" stroke="#8B6914" stroke-width="1"/>
    <line x1="0"  y1="30" x2="80" y2="30" stroke="#8B6914" stroke-width="1"/>
    <rect x="2" y="2" width="76" height="40" rx="3" fill="none" stroke="rgba(255,255,255,0.28)" stroke-width="1"/>
    <text x="40" y="-7" text-anchor="middle" font-size="11" fill="#8B6914" font-family="DM Sans,sans-serif" font-weight="500">CRATE</text>
    <g id="crate-slots">
      <circle id="cs0"  cx="10" cy="10" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs1"  cx="26" cy="10" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs2"  cx="42" cy="10" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs3"  cx="58" cy="10" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs4"  cx="70" cy="10" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs5"  cx="10" cy="24" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs6"  cx="26" cy="24" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs7"  cx="42" cy="24" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs8"  cx="58" cy="24" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs9"  cx="70" cy="24" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs10" cx="10" cy="38" r="5" fill="rgba(0,0,0,0.1)"/>
      <circle id="cs11" cx="26" cy="38" r="5" fill="rgba(0,0,0,0.1)"/>
    </g>
  </g>

  <!-- Loader character – positioned relative to crate; stands just right of crate -->
  <!-- Crate right edge is at 378+80=458; loader centred at 478 -->
  <g id="loader-char" transform="translate(478,267)">
    <!-- Zzz bubble -->
    <g id="loader-zzz" opacity="1">
      <text class="zzz-letter" x="14" y="-2"  font-size="10" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
      <text class="zzz-letter" x="20" y="-10" font-size="12" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
      <text class="zzz-letter" x="27" y="-20" font-size="14" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">Z</text>
    </g>
    <!-- Sleep halo -->
    <circle id="loader-halo" cx="0" cy="6" r="17" fill="rgba(136,170,255,0.1)" stroke="rgba(136,170,255,0.28)" stroke-width="1" opacity="1"/>
    <ellipse cx="0" cy="50" rx="14" ry="5" fill="#00000020"/>
    <rect x="-10" y="20" width="20" height="26" rx="4" fill="#e63946" id="loader-body"/>
    <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#d4a574" stroke-width="1"/>
    <rect x="-12" y="3"  width="24" height="6" rx="2" fill="#a0222c"/>
    <rect x="-7"  y="-4" width="14" height="9" rx="2" fill="#a0222c"/>
    <circle cx="-4" cy="13" r="2" fill="#333"/>
    <circle cx="4"  cy="13" r="2" fill="#333"/>
    <rect id="loader-arm-l" x="-22" y="22" width="13" height="6" rx="3" fill="#e63946"/>
    <rect id="loader-arm-r" x="9"   y="22" width="13" height="6" rx="3" fill="#e63946"/>
    <rect x="-9" y="44" width="8" height="13" rx="3" fill="#7a0e17"/>
    <rect x="2"  y="44" width="8" height="13" rx="3" fill="#7a0e17"/>
    <text x="0" y="70" text-anchor="middle" font-size="10" fill="#e63946" font-family="DM Sans,sans-serif" font-weight="500">LOADER</text>
  </g>
</g>

<!-- Fence posts -->
<g stroke="#5a3010" stroke-width="2" opacity="0.35">
  <line x1="50"  y1="315" x2="50"  y2="365"/>
  <line x1="100" y1="315" x2="100" y2="365"/>
  <line x1="50"  y1="332" x2="100" y2="332"/>
  <line x1="50"  y1="348" x2="100" y2="348"/>
  <line x1="800" y1="315" x2="800" y2="365"/>
  <line x1="850" y1="315" x2="850" y2="365"/>
  <line x1="800" y1="332" x2="850" y2="332"/>
  <line x1="800" y1="348" x2="850" y2="348"/>
</g>

<!-- Birds -->
<g stroke="#334" stroke-width="1.5" fill="none" opacity="0.35">
  <path d="M400,72 Q405,67 410,72"/>
  <path d="M416,66 Q421,61 426,66"/>
  <path d="M542,82 Q547,77 552,82"/>
</g>

<!-- === WORKERS (on top of everything) === -->

<!-- WORKER 0 – blue -->
<g id="worker0" style="transform: translate(310px,268px)">
  <g id="w0-zzz" opacity="0">
    <text class="zzz-letter" x="14" y="-2"  font-size="10" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
    <text class="zzz-letter" x="20" y="-10" font-size="12" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
    <text class="zzz-letter" x="27" y="-20" font-size="14" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">Z</text>
  </g>
  <circle id="w0-halo" cx="0" cy="6" r="17" fill="rgba(136,170,255,0.1)" stroke="rgba(136,170,255,0.28)" stroke-width="1" opacity="0"/>
  <ellipse cx="0" cy="50" rx="14" ry="5" fill="#00000020"/>
  <rect x="-10" y="20" width="20" height="26" rx="4" fill="#4cc9f0" id="w0-body"/>
  <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#d4a574" stroke-width="1"/>
  <rect x="-12" y="3"  width="24" height="6" rx="2" fill="#2a8fb5"/>
  <rect x="-7"  y="-4" width="14" height="9" rx="2" fill="#2a8fb5"/>
  <circle cx="-4" cy="13" r="2" fill="#333"/>
  <circle cx="4"  cy="13" r="2" fill="#333"/>
  <rect x="-22" y="22" width="13" height="6" rx="3" fill="#4cc9f0"/>
  <rect x="9"   y="22" width="13" height="6" rx="3" fill="#4cc9f0"/>
  <rect x="-9" y="44" width="8" height="13" rx="3" fill="#2563a0"/>
  <rect x="2"  y="44" width="8" height="13" rx="3" fill="#2563a0"/>
  <circle id="w0-fruit" cx="18" cy="22" r="7" fill="#e63946" stroke="#c0303a" stroke-width="1.5" opacity="0"/>
  <text x="0" y="70" text-anchor="middle" font-size="10" fill="#4cc9f0" font-family="DM Sans,sans-serif" font-weight="500">P1</text>
</g>

<!-- WORKER 1 – orange -->
<g id="worker1" style="transform: translate(340px,268px)">
  <g id="w1-zzz" opacity="0">
    <text class="zzz-letter" x="14" y="-2"  font-size="10" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
    <text class="zzz-letter" x="20" y="-10" font-size="12" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
    <text class="zzz-letter" x="27" y="-20" font-size="14" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">Z</text>
  </g>
  <circle id="w1-halo" cx="0" cy="6" r="17" fill="rgba(136,170,255,0.1)" stroke="rgba(136,170,255,0.28)" stroke-width="1" opacity="0"/>
  <ellipse cx="0" cy="50" rx="14" ry="5" fill="#00000020"/>
  <rect x="-10" y="20" width="20" height="26" rx="4" fill="#f77f00" id="w1-body"/>
  <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#d4a574" stroke-width="1"/>
  <rect x="-12" y="3"  width="24" height="6" rx="2" fill="#b35c00"/>
  <rect x="-7"  y="-4" width="14" height="9" rx="2" fill="#b35c00"/>
  <circle cx="-4" cy="13" r="2" fill="#333"/>
  <circle cx="4"  cy="13" r="2" fill="#333"/>
  <rect x="-22" y="22" width="13" height="6" rx="3" fill="#f77f00"/>
  <rect x="9"   y="22" width="13" height="6" rx="3" fill="#f77f00"/>
  <rect x="-9" y="44" width="8" height="13" rx="3" fill="#8b4500"/>
  <rect x="2"  y="44" width="8" height="13" rx="3" fill="#8b4500"/>
  <circle id="w1-fruit" cx="18" cy="22" r="7" fill="#f4845f" stroke="#d06040" stroke-width="1.5" opacity="0"/>
  <text x="0" y="70" text-anchor="middle" font-size="10" fill="#f77f00" font-family="DM Sans,sans-serif" font-weight="500">P2</text>
</g>

<!-- WORKER 2 – purple -->
<g id="worker2" style="transform: translate(370px,268px)">
  <g id="w2-zzz" opacity="0">
    <text class="zzz-letter" x="14" y="-2"  font-size="10" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
    <text class="zzz-letter" x="20" y="-10" font-size="12" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">z</text>
    <text class="zzz-letter" x="27" y="-20" font-size="14" fill="rgba(170,196,255,0.9)" font-family="DM Sans,sans-serif">Z</text>
  </g>
  <circle id="w2-halo" cx="0" cy="6" r="17" fill="rgba(136,170,255,0.1)" stroke="rgba(136,170,255,0.28)" stroke-width="1" opacity="0"/>
  <ellipse cx="0" cy="50" rx="14" ry="5" fill="#00000020"/>
  <rect x="-10" y="20" width="20" height="26" rx="4" fill="#9b5de5" id="w2-body"/>
  <circle cx="0" cy="12" r="11" fill="#f5cba7" stroke="#d4a574" stroke-width="1"/>
  <rect x="-12" y="3"  width="24" height="6" rx="2" fill="#6a1fb0"/>
  <rect x="-7"  y="-4" width="14" height="9" rx="2" fill="#6a1fb0"/>
  <circle cx="-4" cy="13" r="2" fill="#333"/>
  <circle cx="4"  cy="13" r="2" fill="#333"/>
  <rect x="-22" y="22" width="13" height="6" rx="3" fill="#9b5de5"/>
  <rect x="9"   y="22" width="13" height="6" rx="3" fill="#9b5de5"/>
  <rect x="-9" y="44" width="8" height="13" rx="3" fill="#4a1280"/>
  <rect x="2"  y="44" width="8" height="13" rx="3" fill="#4a1280"/>
  <circle id="w2-fruit" cx="18" cy="22" r="7" fill="#e63946" stroke="#c0303a" stroke-width="1.5" opacity="0"/>
  <text x="0" y="70" text-anchor="middle" font-size="10" fill="#9b5de5" font-family="DM Sans,sans-serif" font-weight="500">P3</text>
</g>

</svg>
</div>
</div>

<div class="bottom-grid">
  <div id="log-panel">
    <h3>Event Log</h3>
    <div id="log-entries"></div>
  </div>
  <div class="stats-panel">
    <div class="thread-badges">
      <div class="thread-badges-label">Thread states</div>
      <div class="badges-row">
        <div class="tbadge sleeping" id="badge-p0"><div class="dot"></div><span>P1 💤</span></div>
        <div class="tbadge sleeping" id="badge-p1"><div class="dot"></div><span>P2 💤</span></div>
        <div class="tbadge sleeping" id="badge-p2"><div class="dot"></div><span>P3 💤</span></div>
        <div class="tbadge sleeping" id="badge-loader"><div class="dot"></div><span>Loader 💤</span></div>
      </div>
    </div>
    <div class="stat-card">
      <div>
        <div class="stat-label">Fruits picked</div>
        <div class="stat-value" id="stat-fruits">0</div>
      </div>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#e63946" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 3 Q14 8 12 12"/></svg>
    </div>
    <div class="stat-card">
      <div>
        <div class="stat-label">Crate filled</div>
        <div class="stat-value" id="stat-crate">0 / 12</div>
      </div>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#c8a96e" stroke-width="1.5" stroke-linecap="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
    </div>
    <div class="progress-wrap">
      <div class="progress-label"><span>Total progress</span><span id="stat-pct">0%</span></div>
      <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
    </div>
  </div>
</div>

<script>
// ─── Layout constants ─────────────────────────────────────────────────────────
// Absolute SVG coords for each worker's home position
const HOME = [[310,268],[340,268],[370,268]];
// Where pickers walk to at the tree (staggered so they don't overlap)
const TREE_X = [148, 162, 178];
const TREE_Y = 268;
// Where pickers walk to drop fruit (near crate left edge)
const CRATE_DROP_X = [355, 370, 385];
const CRATE_DROP_Y = 268;
// Walk timing
const WALK_MS   = 750;
const RETURN_MS = 600;
// Crate group resting translate
const CAL_REST_X = 0;
// How far right the cal group slides to meet the truck door
// Truck is at SVG x=585; its door is at 585+40=625.
// Crate right edge at rest: 378+80=458. We want crate to slide to ~530.
const CAL_SLIDE_DX = 155;

// ─── State ────────────────────────────────────────────────────────────────────
let fruitsPicked = 0, crateSlot = 0, totalFruits = 12;
const uidToWorker = {};
let nextWorkerIdx = 0;

function getWorkerIdx(uid) {
  const key = (uid !== null && uid !== undefined) ? String(uid) : '__anon' + (nextWorkerIdx % 3);
  if (!(key in uidToWorker)) { uidToWorker[key] = nextWorkerIdx++ % 3; }
  return uidToWorker[key];
}

// ─── Worker position helpers ──────────────────────────────────────────────────
function moveWorkerTo(wi, x, y, ms) {
  const el = document.getElementById('worker' + wi);
  if (!el) return;
  el.style.transition = `transform ${ms}ms cubic-bezier(0.4,0,0.2,1)`;
  el.style.transform  = `translate(${x}px,${y}px)`;
}

// ─── Sleep / wake ─────────────────────────────────────────────────────────────
function setSleep(wi, sleeping) {
  // wi = 0|1|2 for pickers, 'loader' for loader
  const isLoader = wi === 'loader';
  const zzzId    = isLoader ? 'loader-zzz' : 'w' + wi + '-zzz';
  const haloId   = isLoader ? 'loader-halo' : 'w' + wi + '-halo';
  const bodyId   = isLoader ? 'loader-body' : 'w' + wi + '-body';

  const zzz  = document.getElementById(zzzId);
  const halo = document.getElementById(haloId);
  const body = document.getElementById(bodyId);

  if (zzz)  { zzz.style.transition  = 'opacity 0.4s'; zzz.setAttribute('opacity', sleeping ? '1' : '0'); }
  if (halo) { halo.style.transition = 'opacity 0.4s'; halo.setAttribute('opacity', sleeping ? '1' : '0'); }
  if (body) { body.style.transition = 'opacity 0.4s'; body.setAttribute('opacity', sleeping ? '0.45' : '1'); }
}

// ─── Badge helper ─────────────────────────────────────────────────────────────
function setBadge(id, state, text) {
  const el = document.getElementById('badge-' + id);
  if (!el) return;
  el.className = 'tbadge ' + state;
  el.querySelector('span').textContent = text;
}

// ─── Fruit helpers ────────────────────────────────────────────────────────────
function popTreeFruit(fi) {
  const f = document.getElementById('f' + fi);
  if (!f) return;
  f.style.transition = 'r 0.2s ease, opacity 0.4s ease';
  f.setAttribute('r', '14');
  setTimeout(() => { f.setAttribute('r', '0'); f.setAttribute('opacity', '0'); }, 180);
  setTimeout(() => f.remove(), 600);
}

function showHandFruit(wi, show) {
  const f = document.getElementById('w' + wi + '-fruit');
  if (f) { f.style.transition = 'opacity 0.2s'; f.setAttribute('opacity', show ? '1' : '0'); }
}

function fillCrateSlot(slot) {
  const s = document.getElementById('cs' + slot);
  if (s) { s.setAttribute('fill','#e63946'); s.setAttribute('r','6'); }
}

function clearCrateSlots() {
  for (let i = 0; i < 12; i++) {
    const s = document.getElementById('cs' + i);
    if (s) { s.setAttribute('fill','rgba(0,0,0,0.1)'); s.setAttribute('r','5'); }
  }
}

function shakeCrate() {
  const g = document.getElementById('crate-group');
  if (!g) return;
  const seq = [
    'translate(0,0) rotate(-1deg)',
    'translate(3px,0) rotate(1deg)',
    'translate(-2px,0)',
    'translate(2px,0)',
    'translate(0,0)'
  ];
  seq.forEach((s, i) => setTimeout(() => { g.style.transform = `translate(378px,283px) ${s}`; }, i * 65));
  setTimeout(() => { g.style.transform = 'translate(378px,283px)'; }, seq.length * 65 + 50);
}

// ─── Loader + crate group slide ───────────────────────────────────────────────
const calGroup = document.getElementById('cal');

function calSlideToTruck(ms) {
  calGroup.style.transition = `transform ${ms}ms cubic-bezier(0.4,0,0.2,1)`;
  calGroup.style.transform  = `translate(${CAL_SLIDE_DX}px,0)`;
}

function calSlideBack(ms) {
  calGroup.style.transition = `transform ${ms}ms cubic-bezier(0.4,0,0.2,1)`;
  calGroup.style.transform  = 'translate(0,0)';
}

// Raise / lower loader arms
function setLoaderArms(raised) {
  const al = document.getElementById('loader-arm-l');
  const ar = document.getElementById('loader-arm-r');
  if (al) al.setAttribute('y', raised ? '10' : '22');
  if (ar) ar.setAttribute('y', raised ? '10' : '22');
}

// ─── Truck ────────────────────────────────────────────────────────────────────
function truckPullAwayAndReturn() {
  const t = document.getElementById('truck');
  if (!t) return;
  t.style.transition = 'transform 1.3s cubic-bezier(0.4,0,0.8,1)';
  t.style.transform  = 'translate(330px,0)';
  setTimeout(() => {
    t.style.transition = 'none';
    t.style.transform  = 'translate(-360px,0)';
    requestAnimationFrame(() => requestAnimationFrame(() => {
      t.style.transition = 'transform 1.1s cubic-bezier(0.2,0,0.4,1)';
      t.style.transform  = 'translate(0,0)';
    }));
  }, 1500);
}

// ─── Stats ────────────────────────────────────────────────────────────────────
function updateStats() {
  document.getElementById('stat-fruits').textContent = fruitsPicked;
  document.getElementById('stat-crate').textContent  = crateSlot + ' / 12';
  const pct = totalFruits > 0 ? Math.round(fruitsPicked / totalFruits * 100) : 0;
  document.getElementById('stat-pct').textContent = pct + '%';
  document.getElementById('progress-fill').style.width = pct + '%';
}

function addLog(actor, event, wi) {
  const panel = document.getElementById('log-entries');
  const d     = document.createElement('div');
  d.className = 'log-entry';
  const tc  = actor === 'LOADER' ? 'tag-loader' : 'tag-picker' + wi;
  const lbl = actor === 'LOADER' ? 'LOADER' : 'P' + (wi + 1);
  d.innerHTML = `<span class="tag ${tc}">${lbl}</span><span>${event.replace('EventType.','').replace(/_/g,' ')}</span>`;
  panel.prepend(d);
  while (panel.children.length > 60) panel.removeChild(panel.lastChild);
}

function updatePill(t, c) {
  const p = document.getElementById('status-pill');
  p.textContent = t; p.className = c || '';
}

// ─── Picker animation sequence ────────────────────────────────────────────────
function onPickFruit(wi) {
  // Wake
  setSleep(wi, false);
  setBadge('p'+wi, 'active', `P${wi+1} → 🌳`);

  // Walk to tree
  moveWorkerTo(wi, TREE_X[wi], TREE_Y, WALK_MS);

  // Pop fruit, grab it, walk back
  const fi = fruitsPicked - 1;
  setTimeout(() => {
    if (fi >= 0) popTreeFruit(fi);
    showHandFruit(wi, true);
    setBadge('p'+wi, 'active', `P${wi+1} ← 🍎`);
    moveWorkerTo(wi, CRATE_DROP_X[wi], CRATE_DROP_Y, WALK_MS);
  }, WALK_MS + 100);
}

function onAddToCrate(wi) {
  showHandFruit(wi, false);
  setBadge('p'+wi, 'active', `P${wi+1} dropping`);
  fillCrateSlot(crateSlot - 1);
  shakeCrate();

  // Walk home
  setTimeout(() => {
    moveWorkerTo(wi, HOME[wi][0], HOME[wi][1], RETURN_MS);

    setTimeout(() => {
      const done = fruitsPicked >= totalFruits;
      if (done) {
        setBadge('p'+wi, 'done', `P${wi+1} done`);
        setSleep(wi, false);
      } else {
        // Waiting to acquire semaphore slot
        setBadge('p'+wi, 'sleeping', `P${wi+1} 💤`);
        setSleep(wi, true);
      }
    }, RETURN_MS + 200);
  }, 250);
}

// ─── Loader animation sequence ────────────────────────────────────────────────
function onStartTruckLoad() {
  setSleep('loader', false);
  setBadge('loader', 'active', 'Loader → 🚛');
  setLoaderArms(true);

  // Slide crate + loader to truck
  calSlideToTruck(1100);

  // Truck eases in to dock, then leaves
  setTimeout(truckPullAwayAndReturn, 400);
}

function onEmptyCrate() {
  // Slide back
  calSlideBack(900);
  setLoaderArms(false);
  clearCrateSlots();

  setTimeout(() => {
    const done = fruitsPicked >= totalFruits;
    if (done) {
      setBadge('loader', 'done', 'Loader done');
      setSleep('loader', false);
    } else {
      setBadge('loader', 'sleeping', 'Loader 💤');
      setSleep('loader', true);
    }
    // Wake all sleeping pickers (crate has space again)
    for (let i = 0; i < 3; i++) {
      const b = document.getElementById('badge-p' + i);
      if (b && b.className.includes('sleeping') && fruitsPicked < totalFruits) {
        setSleep(i, false);
        setBadge('p'+i, 'waiting', `P${i+1} ready`);
      }
    }
  }, 950);
}

// ─── Poll ─────────────────────────────────────────────────────────────────────
async function poll() {
  try {
    const r = await fetch('/state');
    if (r.ok) {
      const events = await r.json();
      for (const ev of events) {
        totalFruits  = ev.total_fruits  || totalFruits;
        fruitsPicked = ev.fruits_picked;
        crateSlot    = ev.crate_slot_number;

        const actor = ev.actor;
        const uid   = ev.uid != null ? ev.uid : null;
        const wi    = actor === 'LOADER' ? null : getWorkerIdx(uid);

        addLog(actor, ev.event, wi);
        updatePill('Running…', 'loading');
        updateStats();

        if (actor === 'PICKER') {
          if (ev.event.includes('pick_fruit'))   onPickFruit(wi);
          if (ev.event.includes('add_to_crate')) onAddToCrate(wi);
        } else {
          if (ev.event.includes('start_truck_load')) onStartTruckLoad();
          if (ev.event.includes('empty_crate'))      onEmptyCrate();
        }

        if (fruitsPicked >= totalFruits && crateSlot === 0) {
          updatePill('Done! 🎉', 'done');
        }
      }
    }
  } catch(e) {}
  setTimeout(poll, 250);
}

// Start all pickers sleeping (semaphore not yet acquired)
setSleep(0, true); setSleep(1, true); setSleep(2, true); setSleep('loader', true);
poll();
</script>
</body>
</html>
"""

_event_queue = []

@app.route('/update', methods=['POST'])
def update_state():
    data = request.json
    _event_queue.append(data)
    print(f"[{data['actor']}] Event: {data['event']} | Slot: {data['crate_slot_number']} | Total: {data['fruits_picked']}")
    return jsonify({"status": "success"}), 200

@app.route('/state', methods=['GET'])
def get_state():
    events = _event_queue.copy()
    _event_queue.clear()
    return jsonify(events)

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(port=5000)