import { useEffect, useState } from 'react';

const QUERY = '(prefers-reduced-motion: reduce)';
const read = (): boolean => typeof window !== 'undefined' && !!window.matchMedia?.(QUERY).matches;

/** prefers-reduced-motion, live. `force` overrides it (a test or a preview). With it the Reveal has no arrival sweep, no fade and no transition. */
export function usePrefersReducedMotion(force?: boolean): boolean {
  const [rm, setRm] = useState<boolean>(read);
  useEffect(() => {
    if (force !== undefined) return;
    const mq = window.matchMedia?.(QUERY);
    if (!mq) return;
    const on = () => setRm(mq.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [force]);
  return force ?? rm;
}
