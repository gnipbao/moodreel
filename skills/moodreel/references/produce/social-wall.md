# The social wall (社媒口碑墙)

A product's word of mouth as a 4K film: its real posts, each recorded as its platform shows it, as cards on a wall in
perspective under one line of title ("创作者都在聊 YouMind"). One sentence starts it: "做一面 YouMind 的口碑墙", "make a
word-of-mouth wall for YouMind".

## The flow

1. `moodreel wall search <product>` searches YouTube and Bilibili, which need no login. It writes the candidates to
   `out/walls/<product>/`:
   - `candidates.json`;
   - a numbered contact sheet, `candidates.jpg`;
   - a table, `CANDIDATES.md`, with the author, views, date and length of each post.

   Show the user the sheet and the table. Three flags matter:
   - **官方** marks the product's own account. Its posts are announcements, not word of mouth.
   - **禁止转载** means the uploader marked the post "no reprint without permission".
   - **推广** marks a post that says it is paid for ("Includes paid promotion", #ad, 赞助).

   The search sees only a video's description snippet, so recording checks each post's own text again.
2. The user picks posts by number, in the order the wall will show them. Nothing is recorded before the user picks.
3. `moodreel wall record <dir> --pick 3,5,8,…` opens each post in its own window, lets it play muted and records the
   post as the platform shows it.
   - A page that fails gets a second try.
   - A post behind a sign-in or a bot check is skipped, and the reason is reported. Each run is logged in `record.json`:
     what was recorded, and what failed and why.
   - Recording a card again replaces it where it stands, so the wall keeps its order.
   - `--at s` starts the video that far in, past an intro.
4. `moodreel wall make <dir>` writes `<dir>/film/<product>-wall.mp4` at 3840 × 2160 and 30 fps.
   - `--lead` sets the words before the name, `--name` the name, and `--duration` the length (5.5 s by default).
   - Record at least a second longer than the film. A clip shorter than the film holds its last frame.
5. Before handing the film over, review stills at the end of the entrance (0.5 s), the middle and the end.
   - Every card should play: no advert, no black first frame, no player covered by a prompt.
   - The title should sit on one line.
   - To redo one card, run `record --pick n` again, then `make --replace`. The old film is kept as `film.prev`.
   - A platform's logo or a black frame in a still may be one beat of a fast cut in the post itself. Look at the card's
     frames in sequence before re-recording it (`film/media/cardNN/`: webm clips seek coarsely).

## The rules

- **Platforms.** Use only platforms that need no login. Never sign in, and never get round a check. Load one page at a
  time, with pauses between pages. A platform's prompt to log in for HD is an offer, not a wall: close it and record
  the post as it is.
- **Rights.**
  - The posts are their authors' work. The user picks them and answers for showing them.
  - Every card is listed in the film's CREDITS and `media/manifest.json` with its author, link and the date it was
    recorded.
  - A card the uploader marked no-reprint carries that mark.
- **The repository.** Nothing recorded for a wall goes into it: `out/` is ignored, and the repository is public.

## The template (`kit/wall.js`)

The template was measured off a 5.5 s, 4K template film (`out/challenge5`). Values below are in 4K pixels.

| Part | Value |
|---|---|
| Ground | `#000` |
| Grid | 2 px lines every 96 px, at luma 12 (`#0c0c0c`). Fixed to the frame, centred. |
| Title, placement | Centred on x 1915. The ink runs from y 92 to y 225. |
| Title, CJK lead | PingFang SC 500, 141 px, condensed to 0.75. White `#fdfdfd`. |
| Title, Latin name | Avenir Next Condensed 500, 151 px, condensed to 0.85, baseline 6 px lower. Accent `#7498f7`. A CJK name keeps the lead's face. |
| Title, slant | 0.17 (about 9.6°) for both parts. |
| Wall | CSS perspective 3000 px from the frame's centre. |
| Rows | 679 px tall at most, 31 px apart, each centred. |
| Cards | Each keeps its recording's aspect ratio. Corner radius 3.6 % of the card's height. |
| Box | 3000 × 1389. The layout chooses the number of rows that makes the cards largest inside it. The reference's portrait cards fill rows of 679 px within 2902 px; wider cards spread to 3000 px, keeping the reference's side margins (about 445 and 560 px). |
| Camera | Yaw `10.3° − 0.727°·t` (the left side nearer, coming round to face the viewer). Scale `0.983 + 0.0066·t`. The wall's centre at `(64 − 8.7·t, 49)` px from the frame's centre. |
| Entrance | Reading order, top row first. A card every 35 ms, opacity eased out (quart) over 0.467 s. |

**Fit.** The template was checked against a calibration film: the reference's 13 cards replaced by grey stand-ins of
the same widths, compared frame by frame.

| Check | Result |
|---|---|
| Card boxes at 0.5, 2.5 and 5.3 s | Within 1–5 px of the reference's, except where the reference's dark cards were only partly detected. |
| The wall's outline | Within 4–12 px through the clip. |
| Title | Within 5 px. |
| Grid | Exact. |
| Card fades | Each card starts on the same frame, and the values match within 0.05. |

**Portrait or landscape.** Portrait posts (Shorts) give the template's look. Wider posts make wider cards, so the rows
are shorter and there may be more of them.
- A YouTube video's page is recorded at a phone's width, so its card is nearly square (about 0.9).
- Bilibili's page doesn't narrow below its player, so its card is landscape (about 1.5).
- With seven Shorts, five video pages and one Bilibili post, the YouMind wall's rows came to 78 % of the reference's.

## Recording

- **Window size.** Screencasts in headless Chrome come at one pixel per CSS pixel, whatever the device scale. Each
  window is therefore large enough that a card is shrunk on a 4K wall, never enlarged.

  | Post | Window | What the card keeps |
  |---|---|---|
  | Shorts | 900 × 1240 | The player and its action column |
  | YouTube video | 560 × 1240 | The player, title, channel and description, at a phone's width |
  | Bilibili | 1600 × 1240 | The title, stats and player |

- **Interface language.** It follows `--lang` (default `en-US`), through YouTube's `hl` parameter and the
  `Accept-Language` header.
- **Proxy.** The proxy in `HTTPS_PROXY` is the browser's.
- **Adverts.** An advert before a video is waited out, or skipped when the player offers to.
