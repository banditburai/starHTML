/**
 * StarHTML Handlers
 */

export { default as persistPlugin } from "./persist.js";
export { default as scrollPlugin } from "./scroll.js";
export { default as resizePlugin } from "./resize.js";

import persistPlugin from "./persist.js";
import resizePlugin from "./resize.js";
import scrollPlugin from "./scroll.js";

export const persist = persistPlugin;
export const scroll = scrollPlugin;
export const resize = resizePlugin;
