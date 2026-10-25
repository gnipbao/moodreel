// One film, several versions: `moodreel film deliver <film> --variant NAME` (or --all-variants) renders the film with
// film.json's variants[NAME] as window.VARIANT, which the page reads here. Keep every difference a parameter: a
// palette, a seed, a line of text, a length; the picture code stays one.
export const VARIANT = globalThis.VARIANT || {};

// the variant's value for `key`, or the film's own
export const pick = (key, fallback) => (key in VARIANT ? VARIANT[key] : fallback);
