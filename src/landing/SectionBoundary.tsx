import { Component, type ReactNode } from 'react';

/** A section whose chunk cannot be loaded (src/landing/lazy.ts) is missing from the page; the page around it stays. Without this a
 *  rejected import unmounts the whole React root, and the prerendered first screen is already gone by then. */
export class SectionBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true };
  }

  render(): ReactNode {
    return this.state.failed ? null : this.props.children;
  }
}
