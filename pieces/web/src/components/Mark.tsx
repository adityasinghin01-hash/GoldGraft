import { MARK } from '../world/mark';

/** The GoldGraft mark: rootstock + scion joined at a sealed diagonal cut, inside a seal ring. */
export function Mark({ size = 28, title }: { size?: number; title?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" role={title ? 'img' : undefined} aria-hidden={title ? undefined : true} aria-label={title}>
      <circle cx={MARK.ring.cx} cy={MARK.ring.cy} r={MARK.ring.r} stroke="currentColor" strokeOpacity="0.55" strokeWidth="1.6" />
      <path d={MARK.root} stroke="currentColor" strokeWidth="5.4" strokeLinecap="round" />
      <path d={MARK.scion} stroke="currentColor" strokeWidth="3.6" strokeLinecap="round" />
      <path d={MARK.leaf} fill="currentColor" />
      <path d={MARK.seam} stroke="#F5F3EF" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
