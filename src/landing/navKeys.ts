// The header's navigation, in the order of the page's sections (copy nav.*). The header (./Header.tsx) and the menu dialog of the narrow widths
// (./MenuDialog.tsx) show the same links; it is a module of its own because a component file may export components only (fast refresh).
export const NAV_KEYS = ['reveal', 'wall', 'styles', 'how', 'pricing', 'faq'] as const;
