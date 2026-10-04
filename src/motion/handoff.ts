// The hero's entrance starts on the prerendered first screen (index.html, <div id="shell">) and must not start again when React
// replaces that screen with the live one: the live hero is the same markup, so its CSS animations would begin at zero and the
// headline, the lead and the button would drop back and rise a second time, one to two seconds into the page. This file moves the
// clock instead: each CSS animation of the live hero is set to the time its twin has reached in the shell, and an animation whose
// twin has already finished is finished at once.
//
// Called by src/main.tsx in the very task that takes the shell away. It reads the shell then (the shell is about to go) and does the
// rest in the frame's own animation callback, which runs before that frame is painted: the live hero's animations are created by its
// first style calculation, and forcing that calculation inside the long task of React's first render (which has just built the whole
// page) would make the long task longer for nothing, the browser having to do it a moment later anyway.
//
// Twins are found by what they are, not by name: the animation's name, the pseudo element it runs on (the ring, the bloom, the
// glint) and the position of its element among the hero's elements. Both heroes come from the same component, so the order is the same.

type Twin = { name: string; pseudo: string; at: number };

function describe(hero: Element, a: Animation): Twin | null {
  const e = a.effect as KeyframeEffect | null;
  if (!(a instanceof CSSAnimation) || !e?.target) return null;
  const at = e.target === hero ? -1 : [...hero.querySelectorAll('*')].indexOf(e.target);
  return { name: a.animationName, pseudo: e.pseudoElement ?? '', at };
}

const key = (t: Twin) => `${t.name}|${t.pseudo}|${t.at}`;

/** Make the live hero's animations continue where the shell's hero has got to. Safe to call when there is nothing to do. */
export function adoptIntro(shell: Element, live: Element): void {
  if (typeof document.getAnimations !== 'function') return;
  const from = shell.querySelector('.lp-hero');
  if (!from) return;
  // what the shell's animations have reached, and when (the timeline's clock stands still within a frame)
  const at = document.timeline.currentTime as number | null;
  const running = new Map<string, number>();
  for (const a of from.getAnimations({ subtree: true })) {
    const t = describe(from, a);
    if (t && a.currentTime !== null) running.set(key(t), a.currentTime as number);
  }
  requestAnimationFrame(() => {
    const to = live.querySelector('.lp-hero');
    if (!to) return;
    // the frame that paints the live hero is later than the moment the shell was read: its twin would have moved on by the difference
    const dt = at === null ? 0 : ((document.timeline.currentTime as number | null) ?? at) - at;
    for (const a of to.getAnimations({ subtree: true })) {
      const t = describe(to, a);
      if (!t) continue;
      const was = running.get(key(t));
      if (was !== undefined) a.currentTime = was + dt;
      else a.finish();
    }
  });
}
