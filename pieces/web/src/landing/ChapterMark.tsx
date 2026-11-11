import s from './landing.module.css';

/** "02 ——— The problem": a chapter marker whose line draws itself and whose label types in. */
export function ChapterMark({ n, label }: { n: string; label: string }) {
  return (
    <div className={s.chapter}>
      <span className={`gg-num ${s.chapterNum}`}>{n}</span>
      <span className={s.chapterLine} data-draw aria-hidden />
      <span className="gg-label" data-scramble>{label}</span>
    </div>
  );
}
