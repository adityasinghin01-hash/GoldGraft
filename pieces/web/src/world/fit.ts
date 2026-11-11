import type { Layout, StateDef } from './states';

// Pictures that must stay clear of page content get their layout from the page itself.
// fitState() writes the layout straight into the shared state definition (so it holds even
// before the world has loaded) and asks a running world to redraw with it.

export function fitState(states: StateDef[], id: string, layout: Layout) {
  const def = states.find((s) => s.id === id);
  if (!def) return;
  def.layout = layout;
  window.dispatchEvent(new CustomEvent('gg:relayout'));
}
