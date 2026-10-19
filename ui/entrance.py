"""Full-viewport space entrance. Animation is decorative; entry is a native button."""


def entrance_html():
    # Deterministic star positions avoid visual jumps on Streamlit reruns.
    stars = ''.join(
        f'<i style="left:{(n * 73) % 100}%;top:{(n * 47) % 101}%;'
        f'--size:{1 + n % 3}px;--delay:{-(n % 11)}s"></i>'
        for n in range(130)
    )
    return '''<style>
.space-entry{position:fixed;inset:0;z-index:1000;overflow:hidden;background:#030914;color:#edf5ff;font-family:"Segoe UI",Arial,sans-serif;pointer-events:none;isolation:isolate;}
.space-entry:before{content:"";position:absolute;inset:-20%;background:radial-gradient(ellipse at 70% 45%,#144a6c55,transparent 45%),radial-gradient(ellipse at 25% 25%,#4a397c44,transparent 45%);animation:nebula 5s ease-out both;}
.space-stars{position:absolute;inset:-8%;animation:arrival 5s cubic-bezier(.12,.5,.2,1) both;}
.space-stars i{position:absolute;width:var(--size);height:var(--size);border-radius:50%;background:#c3e1ff;box-shadow:0 0 8px #b7d4ff;animation:twinkle 4s var(--delay) ease-in-out infinite;}
.space-planet{position:absolute;width:140vw;height:140vw;left:-20vw;top:72vh;border-radius:50%;background:radial-gradient(ellipse at 50% 0,#172f4d 0,#081a2c 20%,#02060d 48%);box-shadow:0 -2px 0 #b0e7ff,0 -12px 38px #279fd057,0 -32px 130px #2478ba3b;animation:horizon 5s cubic-bezier(.15,.6,.2,1) both;}
.space-grid{position:absolute;inset:0;opacity:.12;background-image:linear-gradient(#91b2d617 1px,transparent 1px),linear-gradient(90deg,#91b2d617 1px,transparent 1px);background-size:90px 90px;mask-image:linear-gradient(transparent,#000);}
.space-top{position:absolute;top:6vh;left:6vw;right:6vw;display:flex;justify-content:space-between;align-items:center;font-size:13px;letter-spacing:3px;color:#a0bed5;}
.space-mark{display:inline-grid;place-items:center;border:1px solid #92bbd94d;width:44px;height:44px;border-radius:50%;font-size:26px;color:#e0f5ff;}
.space-title{position:absolute;top:23%;left:10%;right:10%;text-align:center;animation:title-in 5s ease-out both;}
.space-title .space-kicker{font-size:clamp(12px,1.1vw,16px);letter-spacing:5px;color:#8cbed6;margin-bottom:20px;}
.space-title h1{font-size:clamp(62px,10vw,150px)!important;font-weight:500!important;line-height:1!important;letter-spacing:-.065em!important;color:#edf5ff!important;margin:0!important;padding:0!important;text-shadow:0 5px 45px #548bb740;}
.space-title p{font-size:clamp(17px,1.7vw,23px)!important;color:#a6bfd4!important;line-height:1.6!important;margin:24px auto 0!important;max-width:580px;}
.space-orbits{position:absolute;width:100%;height:100%;inset:0;opacity:.75;}
.space-orbits .orbital-line{fill:none;stroke:#6cbfe0;stroke-width:.6;opacity:.25;stroke-dasharray:3 10;}
.space-orbits .signal{fill:none;stroke:#92eddb;stroke-width:2;stroke-dasharray:20 900;animation:orbit-signal 7s linear infinite;}
.space-category{position:absolute;display:flex;align-items:center;gap:12px;padding:12px 18px;border:1px solid #6b9ebd45;border-radius:30px;background:#07152399;box-shadow:0 8px 35px #0004;color:#d0e7f5;font-size:15px;letter-spacing:1px;animation:category-in 5s ease-out both;}
.space-category svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:1.4;}
.space-launch{left:16%;top:64%;color:#8de3d8;}.space-incident{right:14%;top:59%;color:#dfb0ed;}.space-report{left:44%;top:77%;color:#9fc9ff;}
.space-engine{transform-origin:center;animation:engine 1.3s ease-in-out infinite;}
.space-ping{transform-origin:12px 12px;animation:ping 3s ease-out infinite;}
.space-bottom{position:absolute;bottom:5vh;left:0;right:0;text-align:center;font-size:13px;letter-spacing:2px;color:#bdd4e6;}

.space-entry-progress{position:absolute;bottom:0;height:2px;background:linear-gradient(90deg,#65dcd2,#8cacff);animation:entry-progress 5s linear both;}
.st-key-enter_space button{position:fixed!important;inset:0!important;width:100vw!important;height:100dvh!important;max-width:none!important;z-index:1001!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;}
.st-key-enter_space button p{position:absolute!important;bottom:11vh!important;left:0!important;right:0!important;color:transparent!important;}
.st-key-enter_space button:hover{background:#9acbff05!important;}
.st-key-enter_space button:focus-visible{outline:3px solid #a0dfef!important;outline-offset:-9px!important;}
@keyframes arrival{from{transform:scale(.75) translateY(-4%);opacity:.25}to{transform:scale(1);opacity:1}}
@keyframes nebula{from{transform:scale(.8);opacity:.1}to{transform:scale(1);opacity:1}}
@keyframes horizon{from{transform:translateY(13vh) scale(.9)}to{transform:translateY(0) scale(1)}}
@keyframes title-in{0%{opacity:0;transform:translateY(24px);filter:blur(6px)}35%{opacity:1;filter:blur(0)}100%{opacity:1;transform:translateY(0)}}
@keyframes category-in{0%,20%{opacity:0;transform:translateY(30px)}100%{opacity:1;transform:translateY(0)}}
@keyframes twinkle{50%{opacity:.25}}
@keyframes orbit-signal{to{stroke-dashoffset:-920}}
@keyframes engine{50%{opacity:.3;transform:scaleY(.65)}}
@keyframes ping{0%{opacity:.9;transform:scale(.4)}100%{opacity:0;transform:scale(1.6)}}
@keyframes entry-progress{from{width:0}to{width:100%}}
@media(max-width:650px){.space-title{top:26%;left:6%;right:6%}.space-top{font-size:10px;letter-spacing:1px}.space-launch{left:7%;top:61%}.space-incident{right:7%;top:70%}.space-report{left:12%;top:79%}.space-category{font-size:12px;padding:9px 14px}.space-title p{max-width:300px}.space-planet{top:78vh}}
@media(prefers-reduced-motion:reduce){.space-entry *,.space-entry:before{animation:none!important;filter:none!important}.space-entry-progress{width:100%}}
</style>
<section class="space-entry" aria-label="Welcome to Launch-Deets. Explore launch history, incidents and reports.">
<div class="space-stars">''' + stars + '''</div><div class="space-grid"></div><div class="space-planet"></div>
<div class="space-top"><span class="space-mark">↗</span><span>LAUNCH RESEARCH / A CONNECTED VIEW</span></div>
<svg class="space-orbits" viewBox="0 0 1440 900" preserveAspectRatio="none" aria-hidden="true"><path class="orbital-line" d="M-100 850 Q720 210 1540 750"/><path class="signal" d="M-100 850 Q720 210 1540 750"/><path class="orbital-line" d="M-100 700 Q700 1150 1540 430"/><path class="signal" style="animation-delay:-3s;stroke:#c0a3e8" d="M-100 700 Q700 1150 1540 430"/></svg>
<div class="space-title"><div class="space-kicker">EVERY EVENT HAS A STORY</div><h1>launch-deets</h1><p>Explore the launches.<br>Understand the incidents. Connect the story.</p></div>
<div class="space-category space-launch"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2Q5 8 8 17h8Q19 8 12 2Z M8 12l-4 7 4-2m8-5 4 7-4-2"/><circle cx="12" cy="9" r="2"/><path class="space-engine" d="M10 18l2 5 2-5" stroke="#ffbf7b"/></svg>Launches</div>
<div class="space-category space-incident"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle class="space-ping" cx="12" cy="12" r="8"/><path d="M12 7v6m0 3v1"/></svg>Incidents</div>
<div class="space-category space-report"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 2h10l4 4v16H5Z M15 2v5h4 M8 11h8m-8 4h8m-8 4h5"/></svg>Reports</div>
<div class="space-bottom">CLICK ANYWHERE TO ENTER</div><div class="space-entry-progress"></div></section>'''
