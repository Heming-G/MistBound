# Development process

## Starting idea and intention

The student wanted a manageable Python project with an English interface and documentation. After an earlier flower-care prototype, the student chose a fog-covered exploration map and approved limited-use flashes replenished by collecting fragments.

The intended player enjoys exploring and making small choices. The loop is: choose a direction or use a flash, observe a newly visible route and the remaining resource, then choose where to go next.

## Initial implementation

The first playable version used one fixed maze and three fragments. Ordinary sight began at radius 3 and grew after collection; a flash revealed through walls to radius 7. Explored tiles remained dim. It included wall feedback, pause on window switching, restart confirmation, and a final time/step/flash summary.

During developer review, a persistent fog legend and a brightness floor were added for clarity. Stale wall warnings and expired-flash messages were corrected. These were developer findings, not participant observations.

## Real participant trial and response

The student reported feedback from one roommate on 30 October 2026. On 31 October, the student confirmed that they did not explain the controls or gameplay before the roommate first tried it; the roommate explored independently. The exact session date, duration, first actions and completion result were not supplied and are not invented here. The wording below summarizes the reported observations rather than quoting a transcript.

| Reported feedback | Decision | Implemented response |
| --- | --- | --- |
| After two or three plays the map was easy to remember; random maps, fragments and exits might help. | Provide fresh exploration while allowing deliberate replay. | Seeded maze generation randomizes layout, start, four fragments and exit. R retries the current map; N creates a different map number. |
| The illuminated area felt too large; reduce it and add one or two fragments. | Initially tighten sight and add one objective before attempting a larger increase. | The first revision used ordinary radius 2 and flash radius 3, with four fragments and no sight growth. The student later requested restoring the original sight behavior, as recorded below. |
| Time and step counters did not feel meaningful; consider a leaderboard. | Make comparisons meaningful within one map. | Each map has a persistent local top five, ordered by steps then time, with flashes shown as extra information. |

The report mentioned a range of six tiles without specifying radius or diameter. The first revision used the radius-2/radius-3 interpretation agreed in the follow-up discussion, not an additional participant measurement.

On 31 October 2026, the student requested a larger illuminated area and a return to the original sight behavior. Ordinary radius was restored to 3, growing by 0.4 for each fragment; with four fragments its maximum is 4.6. Flash radius was restored to 7. This is a later student design decision, not a new roommate trial finding. Random maps, four fragments and local records remain part of the design. The rules version was advanced to v3, preserving the old v2 records separately so results earned under different visibility rules are not mixed.

The first trial meets the brief's condition of trying the experience before its controls were explained. The revised version has not yet been retested by a participant. Difficulty and whether the new record system motivates replay remain open questions. See `docs/USER_TRIAL.md`.

Later on 31 October, the student said the original sight was still too large and requested a midpoint between the two versions. The current ordinary radius is 2.5 with 0.2 growth per fragment (maximum 3.3); the flash radius is 5. At every collection stage, these are the arithmetic midpoints between the original growing sight and the reduced version's fixed radius 2; flash radius 5 is midway between 7 and 3. The rules version is now v4, retaining earlier records in separate groups. This adjustment comes from the student's feedback, not a claimed participant retest.

## Implementation choices after the trial

### Randomness with constraints

A seeded backtracking algorithm carves connected rooms, then opens a small number of extra walls for loops. The exit is at least 18 walking steps from the start. Each fragment is at least eight walking steps from the start and five from the exit. Fragment pairs are at least five tiles apart in Manhattan distance and eight walking steps apart. This avoids isolated objectives, immediate wins and clusters near the start.

A six-digit seed reproduces the map. The rules-version prefix keeps leaderboard records separate when map or scoring rules change. The generator uses ordered inputs with a local random generator, so replay does not depend on unrelated animation randomness.

### Scarcity without permanent failure

There are two initial flashes and one additional charge per fragment. Normal sight remains available when flashes run out. Revealed paths remain in memory. There are no enemies or mandatory time limits; the challenge comes from route decisions. Time and flash duration pause in help, records, confirmation screens or on loss of focus.

### Fair local records

Different random maps may have very different route lengths, so scores are compared only for the same map and rules. Steps rank first; time to a tenth of a second breaks ties. Flash count is displayed without changing rank. Exact ties retain completion order. Completed runs are recorded once, while retrying or abandoning an unfinished run creates no result.

The score file is local, contains no names and is ignored by Git. Saving uses a temporary file and replacement to protect the previous data if a write fails. Missing files start empty; unreadable files are preserved, and read/write errors produce a session-only board rather than stopping play.

## AI tools and contribution

OpenAI Codex assisted with assignment interpretation, ideas, Python implementation, tests, visual checks and drafting English documentation. The student selected the project, specified Python and English deliverables, reported the roommate's feedback and approved the revisions. The source and documents were produced with substantial AI assistance and still need the student's own review and understanding.

- Kept: remembered fog and limited flashes replenished by collection.
- Changed: a fixed-map exploration demo became a constrained random-map game after participant feedback.
- Iterated: the participant's request initially led to smaller sight without growth. The student then requested restoring the original sight, found that too large, and asked for a midpoint. Codex implemented the intermediate radius and growth values.
- Scope decision: a global leaderboard was replaced by local same-map records so random-map scores are comparable without accounts or a server.

## Verification

All 21 tests pass. They include 50 generated maps checked for connected floors and objective spacing, reproducibility and varied placements, no-flash completion on 10 maps, collision and feedback, midpoint radius-2.5/radius-5 visibility and one-time growth of 0.2 per fragment, reset and new-map confirmation, pause/focus/records behavior, and one-time completion saving. Record tests verify sorting, the five-entry cap, map/rules-version isolation, reloads, invalid data, corruption preservation and simulated write failures.

A separate stress check passed on 1,000 map numbers for connected floors, reachable objectives and minimum spacing from the start. The revised application opened and rendered with the native macOS Cocoa driver. Game-rendered frames of the title, normal sight, flash, pause, confirmation, completion and records screens were visually reviewed, including a full five-entry table. Preview records are isolated from the real local file. These developer checks do not imply a successful participant retest.

## Development history

Commits preserve the original fixed-map version, the response to roommate feedback (random maps, smaller sight, four fragments and local records), the restoration under v3 rules, and the student's subsequent midpoint adjustment under v4 rules. Further changes after a real retest should be committed with their reasons.

## Publication and verification

The student uploaded the project through GitHub's browser interface to the public repository Heming-G/MistBound. On 31 October 2026, unauthenticated checks confirmed public access and all 22 tracked files matched the local source and assets. The browser upload created one new commit but did not include the existing local development history, and the launcher lost its executable file mode.

The browser upload and local development histories were merged locally without replacing either history. The launcher's executable permission was preserved, and the repository was linked to the existing GitHub remote. On 31 October 2026, after the student authorized the upload and completed GitHub's browser login flow, Codex pushed the prepared history with the official GitHub CLI. Unauthenticated checks confirmed that all existing local commits were visible publicly, all 22 tracked files matched, and the launcher had executable file mode. A backup of the pre-merge history was retained locally outside the project. Canvas submission remains the student's responsibility.
