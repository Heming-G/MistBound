# Credits

- Project direction and design selection: Heming-G.
- Substantial AI assistance with ideas, code, tests and documentation: OpenAI Codex. See PROCESS.md for specific contributions and decisions.
- Runtime graphics and input: **pygame-ce**, imported as `pygame`. Project: <https://github.com/pygame-community/pygame-ce>. Installed dependencies and their exact versions are in `uv.lock`.
- Font: the default font distributed with pygame-ce, loaded using `pygame.font.Font(None, size)`; no font file is separately redistributed in this repository.
- Environment management: **uv** by Astral, <https://docs.astral.sh/uv/>.
- Graphics: original geometric shapes, glow layers, particles and map tiles drawn in Python with AI assistance. No downloaded images, audio or datasets.
- Maze: generated during development from a deterministic sketch, adjusted with loops and stored in this project's source. No third-party map or tutorial code was copied.
- Visibility: an implementation of the standard Bresenham line algorithm checks walls between the player and a tile; flash visibility uses Euclidean distance.
- Requirements: the course's Assignment 3 brief informed the deliverables. The brief itself is not redistributed.
