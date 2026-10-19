"""Original SVG artwork for the home and research pages."""

FRAME_CURSOR_STYLE = '<style>html,body,body *{cursor:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2232%22%20height%3D%2232%22%20viewBox%3D%220%200%2032%2032%22%3E%3Cpath%20d%3D%22M3%202Q19%203%2024%2019L18%2024Q3%2019%203%202Z%22%20fill%3D%22%23eaf6ff%22%20stroke%3D%22%23163e59%22%20stroke-width%3D%222%22%2F%3E%3Cpath%20d%3D%22M8%2016L3%2025L14%2023M17%209L26%204L25%2016%22%20fill%3D%22%2346a9b7%22%20stroke%3D%22%23163e59%22%20stroke-width%3D%221.5%22%2F%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2211%22%20r%3D%223%22%20fill%3D%22%2346a9b7%22%20stroke%3D%22%23163e59%22%2F%3E%3Cpath%20d%3D%22M22%2023L30%2030L26%2021%22%20fill%3D%22%23ed9b42%22%20stroke%3D%22%23163e59%22%2F%3E%3C%2Fsvg%3E") 3 2, pointer!important;}</style>'

def hero_html():
    return '<html><head>' + FRAME_CURSOR_STYLE + '</head><body style="margin:0;background:#101f30"><svg viewBox="0 0 440 390" role="img" aria-label="Spacecraft above an orbital horizon" style="width:100%;height:370px"><defs><radialGradient id="space"><stop stop-color="#173a51"/><stop offset="1" stop-color="#0b1422"/></radialGradient>\n    <linearGradient id="hull" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f5f9ff"/><stop offset=".4" stop-color="#8aabc4"/><stop offset=".7" stop-color="#30485f"/><stop offset="1" stop-color="#bdcedc"/></linearGradient>\n    <linearGradient id="glass"><stop stop-color="#81e7e5"/><stop offset="1" stop-color="#173c59"/></linearGradient>\n    <radialGradient id="glow"><stop stop-color="#7ef4ec" stop-opacity=".35"/><stop offset="1" stop-color="#69e2dd" stop-opacity="0"/></radialGradient></defs><circle cx="240" cy="180" r="180" fill="url(#glow)"/><g fill="none" stroke="#45617b" opacity=".6"><ellipse cx="240" cy="210" rx="190" ry="98" transform="rotate(-28 240 210)"/></g><path d="M0 355Q210 270 440 350" fill="none" stroke="#7294ae"/><g transform="translate(240 180) scale(1.03) rotate(32)">\n      <path d="M-26 45L-82 100l12-62 45-47M26 45l56 55-12-62-45-47" fill="#31495f" stroke="#819aaf"/>\n      <path d="M-23 79l-9 24h64L23 79" fill="#13283c" stroke="#7f9db7"/>\n      <path d="M0-133C-35-100-39-20-29 79Q0 94 29 79C39-20 35-100 0-133" fill="url(#hull)" stroke="#b9cedd"/>\n      <path d="M-20-66Q0-85 20-66L22-42Q0-54-22-42Z" fill="url(#glass)" stroke="#b7edf1"/>\n      <path d="M0-110v28M-28 62h56" stroke="#334c65" fill="none"/>\n      <rect x="-17" y="-18" width="34" height="58" rx="6" fill="#73e2dc" opacity=".75"/>\n      <g class=""><path class="left-door" d="M-18-19H0v60h-18z" fill="#667f94" stroke="#aac1d2"/><path class="right-door" d="M0-19h18v60H0z" fill="#b8cad7" stroke="#d5e2eb"/></g>\n      <text transform="rotate(-90)" x="-37" y="-23" fill="#1c3147" font-size="8" letter-spacing="2">LAUNCH-DEETS</text>\n    </g>\n    </svg></body></html>'

def launch_html(state="idle", reduced=False):
    """Illustrative three-channel animation. It does not represent tool-call counts."""
    state = state if state in {"idle", "working", "complete", "stopped"} else "idle"
    labels = {"idle": "READY FOR YOUR QUESTION", "working": "RESEARCH IN PROGRESS", "complete": "YOUR ANSWER IS READY", "stopped": "RESEARCH FINISHED"}
    paths, cards = [], []
    for x, label, icon, color in [(90, "Records", "▤", "#6ce2cc"), (260, "Reports", "▧", "#79b9ff"), (430, "Incidents", "◇", "#c6a3ff")]:
        path = f"M{x} 465 V420 Q{x} 390 260 365 V315"
        paths.append(f'<g style="--channel:{color}"><path d="{path}" class="wire"/><path d="{path}" class="signal"/></g>')
        if state == "working" and not reduced:
            for delay in (0, .75):
                paths.append(f'<circle r="4" fill="{color}"><animateMotion dur="1.5s" begin="{delay}s" repeatCount="indefinite" path="{path}"/></circle>')
        cards.append(f'<g class="channel-card" style="--channel:{color}"><rect x="{x-66}" y="465" width="132" height="78" rx="12" fill="#152b42" stroke="{color}"/><text x="{x}" y="496" text-anchor="middle" fill="#8fe3e5" font-size="23">{icon}</text><text x="{x}" y="523" text-anchor="middle" fill="#dbe7f2" font-size="17">{label}</text></g>')
    return f"""<!doctype html><html><head>{FRAME_CURSOR_STYLE}<style>
    html,body{{margin:0;background:transparent;font-family:Arial,sans-serif}}svg{{display:block;width:100%;height:590px}}
    .wire{{fill:none;stroke:#2d4d67;stroke-width:2}}.signal{{fill:none;stroke:var(--channel);stroke-width:3;stroke-dasharray:9 15;opacity:0}}
    .working .wire{{stroke:var(--channel);opacity:.35}}.working .channel-card rect{{animation:channelGlow 2s ease-in-out infinite}}
    @keyframes channelGlow{{0%,100%{{fill:#152b42;stroke-opacity:.55}}50%{{fill:#24455b;stroke-opacity:1}}}}
    .working .signal{{opacity:1;animation:flow 1s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-48}}}}
    .flame{{opacity:0;transform-origin:260px 308px;transform:scaleY(.1)}}
    .working .flame{{animation:warmup 5s ease-out forwards}}
    .working .flame-core{{animation:flicker .4s ease-in-out infinite alternate;transform-origin:260px 308px}}
    @keyframes warmup{{0%{{opacity:.85;transform:scaleY(.55)}}50%{{opacity:.95;transform:scaleY(.8)}}100%{{opacity:1;transform:scaleY(1.05)}}}}
    @keyframes flicker{{to{{transform:scaleX(.85)}}}}
    .complete .flame{{opacity:1;transform:scaleY(1.6)}}
    .rocket-flight{{transform-origin:260px 225px}}
    .complete .rocket-flight{{animation:takeoff 2.8s cubic-bezier(.45,0,.8,.5) .25s forwards}}
    @keyframes takeoff{{0%{{transform:translateY(0)}}18%{{transform:translateY(-8px)}}100%{{transform:translateY(-550px)}}}}
    .complete .signal{{opacity:.35;stroke-dasharray:none}}
    .launch-message{{opacity:0}}.complete .launch-message{{animation:arrive .8s ease 4.5s forwards}}
    @keyframes arrive{{to{{opacity:1}}}}
    .idle .pad,.stopped .pad{{opacity:.5}}
    @media(prefers-reduced-motion:reduce){{*{{animation:none!important}}.working .signal{{opacity:.65;stroke-dasharray:none}}.working .flame{{opacity:.4;transform:scaleY(.4)}}.complete .rocket-flight{{transform:translateY(-550px)}}.complete .launch-message{{opacity:1}}}}
    {'*{animation:none!important}.working .signal{opacity:.65;stroke-dasharray:none}.working .flame{opacity:.4;transform:scaleY(.4)}.complete .rocket-flight{transform:translateY(-550px)}.complete .launch-message{opacity:1}' if reduced else ''}
    </style></head><body><svg class="{state}" viewBox="0 0 520 590" role="img" aria-label="{labels[state]}. Illustrative research flow with three channels and a spacecraft.">
    <defs><radialGradient id="back"><stop stop-color="#20425b"/><stop offset="1" stop-color="#0c1b2d"/></radialGradient>
    <linearGradient id="body" x1="0" x2="1"><stop stop-color="#48637b"/><stop offset=".35" stop-color="#eef6ff"/><stop offset=".65" stop-color="#a6bed3"/><stop offset="1" stop-color="#38546e"/></linearGradient>
    <linearGradient id="fire" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#f6feff"/><stop offset=".25" stop-color="#91f5ff"/><stop offset=".55" stop-color="#ffb65d"/><stop offset=".85" stop-color="#ff753e" stop-opacity=".9"/><stop offset="1" stop-color="#ff753e" stop-opacity="0"/></linearGradient>
    <radialGradient id="padGlow"><stop stop-color="#78d8ec" stop-opacity=".3"/><stop offset="1" stop-color="#78d8ec" stop-opacity="0"/></radialGradient></defs>
    <rect width="520" height="590" rx="18" fill="url(#back)"/>
    <g stroke="#355570" fill="none" opacity=".45"><ellipse cx="260" cy="235" rx="190" ry="68" transform="rotate(-25 260 235)"/><circle cx="260" cy="230" r="160" stroke-dasharray="2 12"/></g>
    <g fill="#b6cce1" opacity=".5"><circle cx="80" cy="130" r="1"/><circle cx="430" cy="190" r="1"/><circle cx="390" cy="80" r="1.5"/><circle cx="120" cy="290" r="1"/></g>
    {''.join(paths)}
    <ellipse class="pad" cx="260" cy="340" rx="110" ry="35" fill="url(#padGlow)"/>
    <g class="rocket-flight">
      <g class="flame"><path d="M242 303Q232 350 260 414Q289 348 278 303Z" fill="url(#fire)"/><path class="flame-core" d="M250 303Q245 335 260 375Q276 333 270 303Z" fill="#d9fbff" opacity=".8"/></g>
      <g transform="translate(260 225)">
        <path d="M-25 25L-65 84l9-52 32-31M25 25l40 59-9-52-32-31" fill="#3d5870" stroke="#87a6bd"/>
        <path d="M-23 65l-8 22h62l-8-22" fill="#172d42" stroke="#87a6bd"/>
        <path d="M0-125C-32-91-35-18-27 65Q0 79 27 65C35-18 32-91 0-125" fill="url(#body)" stroke="#adc7da"/>
        <path d="M-19-58Q0-77 19-58L20-36Q0-46-20-36Z" fill="#173d59" stroke="#98e0ec"/>
        <path d="M0-102v23M-26 48h52" stroke="#45627d" fill="none"/>
        <rect x="-15" y="-17" width="30" height="45" rx="4" fill="#91aabe" stroke="#d2e1ed"/>
        <text transform="rotate(-90)" x="-30" y="-20" fill="#233f56" font-size="6" letter-spacing="1.4">LAUNCH-DEETS</text>
      </g>
    </g>
    {''.join(cards)}
    </svg></body></html>"""
