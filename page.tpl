<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="lib/vendor/gsap.min.js"></script>
    <!-- theme -->
    <!-- /theme -->
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--bg); }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--bg); font-family: var(--font); }
      /* The backdrop: bright, sharp and always moving (make_backdrop.py). */
      .bgwrap { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; opacity: 0; }
      .bgwrap video { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
      /* Karaoke captions: two words, centred in y 290-430, inside x 96-926. The spoken word takes the highlight. */
      #caps { position: absolute; left: 96px; top: 290px; width: 830px; height: 140px; z-index: 8; }
      .cap { position: absolute; left: 0; top: 0; width: 830px; height: 140px; display: flex; align-items: center; justify-content: center; text-align: center; color: var(--text); font-weight: var(--weight); letter-spacing: -0.01em; line-height: 1; opacity: 0; white-space: nowrap; }
      .cap .w { display: inline-block; margin: 0 0.12em; -webkit-text-stroke: 11px rgba(11, 11, 16, 0.96); paint-order: stroke fill; text-shadow: 0 8px 22px rgba(0, 0, 0, 0.45); }
      /* The window set: one big desktop window, two small ones under it, the big one's corner over them. */
      .win { position: absolute; z-index: 5; opacity: 0; }
      .win.big { z-index: 6; }
      .bob { position: absolute; inset: 0; border-radius: 16px; overflow: hidden; background: var(--bg); border: 2px solid rgba(245, 245, 247, 0.6); box-shadow: 0 26px 60px rgba(11, 11, 16, 0.5), 0 4px 12px rgba(11, 11, 16, 0.35); }
      .bar { position: absolute; left: 0; top: 0; right: 0; height: 44px; background: rgba(21, 21, 29, 0.94); border-bottom: 1px solid rgba(245, 245, 247, 0.14); display: flex; align-items: center; gap: 10px; padding-left: 18px; }
      .bar i { display: block; width: 13px; height: 13px; border-radius: 50%; background: rgba(245, 245, 247, 0.28); }
      .bar i:first-child { background: var(--highlight); }
      .bar b { position: absolute; right: 18px; top: 50%; width: 64px; height: 6px; margin-top: -3px; border-radius: 3px; background: rgba(245, 245, 247, 0.32); }
      .small .bar, .cell .bar { height: 36px; gap: 8px; padding-left: 14px; }
      .small .bar i, .cell .bar i { width: 10px; height: 10px; }
      .small .bar b, .cell .bar b { right: 14px; width: 40px; height: 5px; }
      .pic { position: absolute; left: 0; right: 0; bottom: 0; top: 44px; overflow: hidden; background: var(--bg); }
      .small .pic, .cell .pic { top: 36px; }
      .pic img, .pic video { position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }
      /* The end card: the client's logo, the CTA line and a sub line, centred in the safe zone (y 500-1250). */
      #end { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; z-index: 7; opacity: 0; }
      #endcard { position: absolute; left: 96px; top: 500px; width: 830px; height: 740px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 34px; text-align: center; }
      #logo { display: block; max-width: 620px; max-height: 360px; object-fit: contain; filter: drop-shadow(0 18px 40px rgba(0, 0, 0, 0.45)); }
      #endline { color: var(--text); font-weight: var(--weight); font-size: 92px; line-height: 1.02; letter-spacing: -0.01em; max-width: 830px; -webkit-text-stroke: 10px rgba(11, 11, 16, 0.96); paint-order: stroke fill; }
      #endsub { color: var(--highlight); font-weight: var(--weight); font-size: 50px; line-height: 1.1; max-width: 830px; -webkit-text-stroke: 8px rgba(11, 11, 16, 0.96); paint-order: stroke fill; }
      #draft { position: absolute; left: 54px; top: 1556px; z-index: 10; padding: 6px 16px; border-radius: 10px; background: rgba(11, 11, 16, 0.7); border: 2px solid var(--highlight); color: var(--highlight); font-weight: var(--weight); font-size: 30px; letter-spacing: 0.08em; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
      <!-- bgs -->
      <!-- /bgs -->
      <!-- wins -->
      <!-- /wins -->
      <!-- end -->
      <!-- /end -->
      <!-- caps -->
      <!-- /caps -->
      <!-- draft -->
      <!-- /draft -->
      <audio id="music" class="clip" src="assets/music/mix.wav" data-start="0" data-duration="__DUR__" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      (function () {
        const DURATION = __DUR__;
        const GROUPS = [];    // [id, from, to, [[word id, from, to], ...]]
        const TOPICS = [];    // [from, to, [[window id, pop delay], ...]]
        const LOOK = {};      // { bob, end_from, has_bg }
        const tl = gsap.timeline({ paused: true });
        const css = getComputedStyle(document.documentElement);
        const ink = css.getPropertyValue("--text").trim();
        const hi = css.getPropertyValue("--highlight").trim();

        // The backdrop runs the whole film.
        if (LOOK.has_bg) tl.set("#bgw0", { opacity: 1 }, 0);

        // Karaoke: a pair of words pops in on its first word; each word takes the highlight exactly on its start and
        // goes back to the text colour when the next one starts; the pair goes when the next pair starts.
        GROUPS.forEach(([id, from, to, ws], i) => {
          if (i === 0) tl.set("#" + id, { opacity: 1 }, 0);
          else tl.fromTo("#" + id, { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: Math.min(0.2, Math.max(to - from, 0.08) * 0.7), ease: "back.out(2)", immediateRender: false }, from);
          tl.set("#" + id, { opacity: 0 }, to);
          ws.forEach(([wid, a, b]) => {
            tl.set("#" + wid, { color: hi }, a);
            if (b < to) tl.set("#" + wid, { color: ink }, b);
          });
        });

        // Windows: one set per topic. The big one pops, the small ones follow a beat apart, a springy scale-in from
        // 0.85; held, each bobs a few px on a sine (never dead still) while its picture drifts; the set goes together.
        TOPICS.forEach(([from, to, wins], ti) => {
          wins.forEach(([id, delay], k) => {
            const at = ti === 0 ? 0 : from + delay;
            const hold = Math.max(to - at, 0.3);
            if (ti === 0) tl.set("#" + id, { opacity: 1 }, 0);
            else tl.fromTo("#" + id, { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.4)", immediateRender: false }, at);
            const half = 1.0, n = Math.max(1, Math.ceil(hold / half));
            const amp = LOOK.bob ?? 2;
            const dir = k % 2 ? -1 : 1;
            tl.fromTo("#" + id + " .bob", { y: -amp * dir }, { y: amp * dir, duration: half, ease: "sine.inOut", repeat: n - 1, yoyo: true, immediateRender: false }, at);
            if (document.querySelector("#" + id + " img")) tl.fromTo("#" + id + " img", { scale: 1.02 }, { scale: 1.07, duration: hold + 0.3, ease: "none", immediateRender: false }, at);
            tl.to("#" + id, { opacity: 0, scale: 0.94, duration: 0.14, ease: "sine.in", immediateRender: false }, to);
          });
        });

        // The end card: fades up over the backdrop as the windows leave, the logo scales in, then the lines follow.
        const E = LOOK.end_from;
        tl.fromTo("#end", { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "sine.out", immediateRender: false }, E);
        if (document.getElementById("logo")) tl.fromTo("#logo", { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.6)", immediateRender: false }, E);
        if (document.getElementById("endline")) tl.fromTo("#endline", { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.5, ease: "back.out(1.4)", immediateRender: false }, E + 0.2);
        if (document.getElementById("endsub")) tl.fromTo("#endsub", { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: "expo.out", immediateRender: false }, E + 0.4);
        // ...and keeps moving slowly so the last frames are never still.
        tl.fromTo("#endcard", { scale: 1 }, { scale: 1.04, duration: Math.max(DURATION - E, 0.1), ease: "none", immediateRender: false }, E);

        tl.set({}, {}, DURATION);
        window.__timelines = window.__timelines || {};
        window.__timelines["main"] = tl;
      })();
    </script>
  </body>
</html>
