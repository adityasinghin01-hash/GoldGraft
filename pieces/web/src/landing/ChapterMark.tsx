import s from './landing.module.css';

/** "——— The problem": a quiet chapter marker. The line draws itself, the word rolls up into place. */
export function ChapterMark({ label }: { label: string }) {
  return (
    <p className={`gg-label ${s.chapter}`}>
      <span className={s.chapterLine} data-draw aria-hidden />
      <span data-split>{label}</span>
    </p>
  );
}
