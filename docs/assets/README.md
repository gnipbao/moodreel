# README artwork

The English and Chinese homepages share an original cover and two excerpts from the example films. Each animation has a still for readers who prefer reduced motion.

| Asset | Where the picture comes from |
| --- | --- |
| [Cover loop](moodreel-motion.webp) · [Still](moodreel-cover.webp) | *24 exposures*. A crescent moves across a fan of translucent film frames as the fan opens and closes over four seconds. The wordmark pairs Archivo with Cormorant Garamond Italic, both from the Signal Plates pack. [Editable scene](cover.html) · [Font credits](../../packs/graphic-type/signal-plates/kit/fonts/OFL.txt) |
| [Swiss Programme](swiss-programme.gif) | Seconds 4.50–10.50 of the 15-second film. A page turn carries the grid into its second rule. [Scene](../../examples/swiss-programme/main.js) · [Film credits](../../examples/swiss-programme/CREDITS) |
| [First Save](first-save.gif) | Seconds 4.25–8.75 of the 10-second film. The character walks, the palette shifts and the save prompt appears. [Scene](../../examples/first-save/main.js) · [Film credits](../../examples/first-save/CREDITS) |

The two example GIFs run at 16 fps. To render the cover with Moodreel, run these commands from the repository root. The scene implements `window.render(t)` and takes its fonts from the adjacent files in the staging folder.

```sh
mkdir -p out/readme-cover
cp docs/assets/cover.html out/readme-cover/index.html
cp packs/graphic-type/signal-plates/kit/fonts/Archivo-var.ttf out/readme-cover/
cp packs/graphic-type/signal-plates/kit/fonts/CormorantGaramond-Italic-var.ttf out/readme-cover/
uv run moodreel render still out/readme-cover 0 --size 1800x672
uv run moodreel render video out/readme-cover --size 1200x448 --fps 15 --engine chrome --out out/readme-cover.mp4
```
