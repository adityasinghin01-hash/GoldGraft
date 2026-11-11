import { useId, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRightIcon } from '@phosphor-icons/react';
import styles from './GlassEntry.module.css';

type Props = { label: string; placeholder: string; action: string; note: string; invalid: string; inputId?: string };

const VALID = /^https?:\/\/\S+$/;

/**
 * The glass Check box (Raycast-style command entry, real form).
 * idle → focused → invalid (inline, nothing sent) → going (opens the Check screen with the address).
 */
export function GlassEntry({ label, placeholder, action, note, invalid, inputId }: Props) {
  const autoId = useId();
  const id = inputId ?? autoId;
  const [value, setValue] = useState('');
  const [error, setError] = useState(false);
  const [going, setGoing] = useState(false);
  const navigate = useNavigate();

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const url = value.trim();
    if (!VALID.test(url)) { setError(true); return; }
    setError(false);
    setGoing(true);
    navigate(`/check?url=${encodeURIComponent(url)}`);
  };

  return (
    <form className={styles.form} onSubmit={submit} noValidate data-error={error || undefined}>
      <label htmlFor={id} className={styles.label}>{label}</label>
      <div className={`gg-glass ${styles.field}`}>
        <span className={styles.glint} aria-hidden />
        <input
          id={id}
          className={styles.input}
          type="url"
          inputMode="url"
          autoComplete="url"
          spellCheck={false}
          placeholder={placeholder}
          value={value}
          onChange={(e) => { setValue(e.target.value); if (error) setError(false); }}
          aria-invalid={error || undefined}
          aria-describedby={`${id}-note`}
        />
        <button type="submit" className={`gg-btn gg-btn--gold ${styles.go}`} disabled={going}>
          {action}
          <ArrowRightIcon size={16} weight="bold" aria-hidden />
        </button>
      </div>
      <p id={`${id}-note`} className={styles.note} role={error ? 'alert' : undefined}>
        {error ? invalid : note}
      </p>
    </form>
  );
}
