import '@testing-library/jest-dom/vitest';

// Mock ResizeObserver for Carbon components
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
