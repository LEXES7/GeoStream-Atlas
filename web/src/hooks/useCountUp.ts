import { useEffect, useRef, useState } from "react";

const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

export function useCountUp(target: number | null | undefined, duration = 1100, decimals = 0) {
  const [value, setValue] = useState(0);
  const frame = useRef<number>();

  useEffect(() => {
    if (target === null || target === undefined || Number.isNaN(target)) {
      setValue(0);
      return;
    }
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      setValue(from + (target - from) * easeOut(p));
      if (p < 1) frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
    return () => {
      if (frame.current) cancelAnimationFrame(frame.current);
    };
  }, [target, duration]);

  if (target === null || target === undefined) return "—";
  return value.toFixed(decimals);
}
