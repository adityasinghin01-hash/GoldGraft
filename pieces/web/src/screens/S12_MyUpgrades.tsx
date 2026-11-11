import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, TrashIcon } from '@phosphor-icons/react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { stageName } from '../copy/words';
import { Empty, PageHead, Tag } from '../components/ui';
import { SeamLoader } from '../components/Loaders';
import { dropUpgrade, readUpgrades, type MyUpgrade } from '../lib/store';
import { formatDate } from '../lib/format';
import s from './s12.module.css';

function StageCell({ graftId }: { graftId: string }) {
  const q = useQuery({ queryKey: ['graft', graftId], queryFn: () => api.graft(graftId), retry: 0 });
  if (q.isPending) return <SeamLoader size={18} label="Loading stage" />;
  if (q.isError) return <Tag>Not found</Tag>;
  const st = String(q.data.stage);
  return <Tag tone={st === 'DONE' ? 'good' : st === 'CUTBACK' || st === 'FAILED' ? 'bad' : 'gold'}>{stageName(st)}</Tag>;
}

export default function S12_MyUpgrades() {
  const [{ list, ok }, setState] = useState(() => readUpgrades());
  useEffect(() => { document.title = 'GoldGraft · My upgrades'; }, []);
  const remove = (id: string) => { dropUpgrade(id); setState(readUpgrades()); };
  const sorted = [...list].sort((a, b) => b.started_at.localeCompare(a.started_at));

  return (
    <div className={`gg-center ${s.screen}`}>
      <PageHead title="My upgrades" explain="Saved in this browser only. Keys are never saved."
        sub={list.length === 1 ? '1 upgrade started in this browser' : `${list.length} upgrades started in this browser`} />
      {!ok && <p className={s.warn}>This browser can't save your list.</p>}
      {sorted.length === 0 ? (
        <Empty title="No upgrades started here yet." action={<Link className="gg-btn gg-btn--gold gg-btn--sm" to="/check">Start</Link>} />
      ) : (
        <ul className={s.list}>
          {sorted.map((u: MyUpgrade, i) => (
            <li key={u.graft_id} className={`gg-glass ${s.row}`} style={{ ['--i' as string]: i }}>
              <Link to={`/g/${u.graft_id}`} className={s.name}>{u.name || u.shop_id} <ArrowRightIcon size={14} /></Link>
              <span className={s.when} title={u.started_at}>Started {formatDate(u.started_at)}</span>
              <StageCell graftId={u.graft_id} />
              <button className={s.remove} onClick={() => remove(u.graft_id)}><TrashIcon size={14} /> Remove</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
