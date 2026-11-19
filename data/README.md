# Shared data

PCB101 keeps nothing here; the folder is left from the course template. Each lab's inputs live in its own package, under `labs/<lab-id>/data/`. For example, Lab 02's `rhl0024a.json` holds the numbers from TI's RHL0024A drawing and the pins in Table 4-1 of the datasheet, and Lab 06's `data/` holds the hashed review key and the seeded board's bring-up plan. Tiny Tapeout's boards aren't kept in the repo: `labs/common/fetch_boards.py` fetches them at pinned commits into `labs/common/upstream/`, which git ignores.

If PCB101 ever needs a dataset that several labs share, it goes here. Put large files in Git LFS or on external hosting, and don't put bulk data under `docs/`.
