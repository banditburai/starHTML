/**
 * StarHTML Handlers
 */

export { default as persistPlugin } from "./persist.js";
export { default as scrollPlugin } from "./scroll.js";
export { default as resizePlugin } from "./resize.js";
export { default as dragPlugin } from "./drag.js";
export { default as canvasPlugin } from "./canvas.js";
export { default as positionPlugin } from "./position.js";
export { default as splitPlugin } from "./split.js";

import canvasPlugin from "./canvas.js";
import dragPlugin from "./drag.js";
import persistPlugin from "./persist.js";
import positionPlugin from "./position.js";
import resizePlugin from "./resize.js";
import scrollPlugin from "./scroll.js";
import splitPlugin from "./split.js";

export const persist = persistPlugin;
export const scroll = scrollPlugin;
export const resize = resizePlugin;
export const drag = dragPlugin;
export const canvas = canvasPlugin;
export const position = positionPlugin;
export const split = splitPlugin;
