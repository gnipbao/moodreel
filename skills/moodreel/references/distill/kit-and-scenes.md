# The kit and the scenes

A style is what makes any frame read as itself: its look, its materials, how its type, light and things move, how its
camera behaves. Its reference's **scenes** are not the style: the particular layouts, set pieces, figures, images and
moments a film used to say its own things. Distil the first; inventory the second and leave it behind. A style that
ships its reference's scenes makes every new film a remix of the reference, however new the subject.

## The inventory (in ANALYSIS.md)

List the reference's set pieces by name, as content: the opening image, each recurring layout, each figure or object
drawn, each staged moment ("an ink drop on black bursting into writing", "a floor of words with tiles standing in
rows", "a moon over the sea with its path", "a monk walking in bamboo"). For each, say which trait of the signature it
carried ("type as matter", "a camera in a world of type"). The trait goes into STYLE.md; the set piece stays here.

## What goes in the kit: primitives

Functions that let a director make the signature happen in a scene of their own:

- **Materials and marks**: grounds, papers, grain, the style's ways of making a mark (grit, stipple, a wash, a
  cut-out, a cell, a brush), each taking any shape or path.
- **How the medium's subject behaves**: for a type style, typing, the signature arrival, type turned to points,
  shattering, jumbling, filling a region with text; for an illustration style, a figure's line, a fill, a shadow.
- **The signature move** as a function with its measured timing.
- **A space to stage in**: a 3D or 2.5D layer with the style's light and fog, planes and objects that carry the medium
  (text on any plane, a character as a block), a camera fitter. Not the reference's staging of it.
- **Tokens**: the measured values as defaults.

## What stays out of the kit: set pieces

A function that draws one of the inventory's scenes (`grove()`, `walker()`, `moonOverSea()`, a page laid out as the
reference's): it is the reference's content, and having it at hand makes films re-stage it. If the remake built them,
keep them in the project's `studies/` (not packed), as evidence of how a trait was achieved. When a set piece holds a
general technique (water in perspective, a stippled mountain), lift the technique into a primitive (`waves(region)`,
`stipple(shape)`) and leave the scene behind.

## Writing STYLE.md §6, §8, §10

- **§6, camera**: the camera's attitude and the kinds of move it makes, each with what it expresses ("pushes are
  sudden and land like the type does", "the camera travels through the medium, not past it"), and as examples only, how
  the reference used them. Not a list of the reference's shots.
- **§8, native moves**: the principles behind what only this style does ("the text becomes what it names", "a word's
  arrival is a blow"), each with one example from the reference and an invitation to invent; never a menu of the
  reference's moments to pick from.
- **§10, engine**: the primitives, with a minimal example that draws a scene the reference doesn't have.

## Checking

- `moodreel scene-check <project> <stills or film>`: each frame's composition against every reference frame. A
  copied composition fails; a close one is a lead to look at. It sees layouts, not ideas: a set piece redrawn in a new
  layout passes the check, so review the demo against the inventory by eye.
- `moodreel motion-check`: the motion's character is the style's; the film's pace (holds, shot lengths, how much of it
  moves) follows its content and comes back as advice.
- The demo shows the signature with scenes invented for its subject, and none of the inventory's set pieces.
