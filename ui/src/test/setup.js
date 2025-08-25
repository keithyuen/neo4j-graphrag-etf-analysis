import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Mock window.ResizeObserver (used by Cytoscape)
global.ResizeObserver = class ResizeObserver {
  constructor(cb) {
    this.cb = cb;
  }
  observe() {
    this.cb([{ borderBoxSize: { inlineSize: 0, blockSize: 0 } }], this);
  }
  unobserve() {}
  disconnect() {}
};

// Mock window.matchMedia (used by some components)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Mock IntersectionObserver (if needed by components)
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  disconnect() {}
  unobserve() {}
};

// Suppress console warnings during tests (optional)
const originalConsoleWarn = console.warn;
console.warn = (...args) => {
  if (
    typeof args[0] === 'string' &&
    args[0].includes('React Router')
  ) {
    return;
  }
  originalConsoleWarn(...args);
};