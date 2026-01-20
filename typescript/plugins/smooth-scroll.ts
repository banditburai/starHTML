/**
 * Smooth Scroll Module - Provides interpolation for scroll values
 */

export interface SmoothScrollConfig {
  factor?: number; // Interpolation factor (0-1), lower = smoother
  threshold?: number; // Minimum difference to trigger updates
}

interface SmoothData {
  scrollY: number;
  velocity: number;
  progress: number;
  pageProgress: number;
  visiblePercent: number;
  rafId?: number;
}

const DEFAULT_SMOOTH_FACTOR = 0.1;
const DEFAULT_UPDATE_THRESHOLD = 0.1;

// Store for smooth scroll values per element
const smoothScrollStore = new WeakMap<HTMLElement, SmoothData>();

// Lerp function for smooth interpolation
export function lerp(start: number, end: number, factor: number): number {
  return start + (end - start) * factor;
}

export class SmoothScroll {
  private element: HTMLElement;
  private config: Required<SmoothScrollConfig>;
  private updateCallback: () => void;
  private rafId: number | null = null;
  private isActive = false;

  constructor(element: HTMLElement, updateCallback: () => void, config: SmoothScrollConfig = {}) {
    this.element = element;
    this.updateCallback = updateCallback;
    this.config = {
      factor: config.factor ?? DEFAULT_SMOOTH_FACTOR,
      threshold: config.threshold ?? DEFAULT_UPDATE_THRESHOLD,
    };
  }

  getSmoothData(rawData: {
    scrollY: number;
    velocity: number;
    progress: number;
    pageProgress: number;
    visiblePercent: number;
  }) {
    // Get or initialize smooth data for this element
    let smoothData = smoothScrollStore.get(this.element);
    if (!smoothData) {
      smoothData = { ...rawData };
      smoothScrollStore.set(this.element, smoothData);
    }

    // Check if update is needed
    const needsUpdate = this.checkNeedsUpdate(smoothData, rawData);

    if (needsUpdate) {
      // Interpolate numeric values
      smoothData.scrollY = lerp(smoothData.scrollY, rawData.scrollY, this.config.factor);
      smoothData.velocity = lerp(smoothData.velocity, rawData.velocity, this.config.factor);
      smoothData.progress = lerp(smoothData.progress, rawData.progress, this.config.factor);
      smoothData.pageProgress = lerp(
        smoothData.pageProgress,
        rawData.pageProgress,
        this.config.factor
      );
      smoothData.visiblePercent = lerp(
        smoothData.visiblePercent,
        rawData.visiblePercent,
        this.config.factor
      );

      // Schedule RAF update if not already scheduled
      if (!this.rafId && this.isActive) {
        this.rafId = requestAnimationFrame(() => this.animationFrame());
      }
    }

    return smoothData;
  }

  private checkNeedsUpdate(smoothData: SmoothData, rawData: typeof smoothData): boolean {
    const threshold = this.config.threshold;
    return (
      Math.abs(smoothData.scrollY - rawData.scrollY) > threshold ||
      Math.abs(smoothData.velocity - rawData.velocity) > threshold ||
      Math.abs(smoothData.progress - rawData.progress) > threshold ||
      Math.abs(smoothData.pageProgress - rawData.pageProgress) > threshold ||
      Math.abs(smoothData.visiblePercent - rawData.visiblePercent) > threshold
    );
  }

  private animationFrame() {
    this.rafId = null;
    this.updateCallback();
  }

  start() {
    this.isActive = true;
  }

  stop() {
    this.isActive = false;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  cleanup() {
    this.stop();
    smoothScrollStore.delete(this.element);
  }
}
