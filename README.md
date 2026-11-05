# LED channel geometry visualizer

[Open the visualizer](https://ramonsaboya.github.io/open-music-led-visualizer/)

Interactive 2D sections and rotatable 3D body, insert and assembly views for
52, 56 and 64 active LEDs on the same physical 8×8, 10 mm-pitch panel.

This snapshot explores a single-stencil body: two white .2 mm layers, one
black .2 mm stencil layer, and an insert whose dividers stop independently
of the surrounding bulk. Compare X=6 (.6 mm gap) and X=9 (1.2 mm gap), or
inspect a reference with dividers continuing to the mating plane.

- Exact undivided mating silhouette at insert layer 67.
- Gradual simplification towards the LED grid, with .4 mm initial clearance.
- One .2 mm pin layer; no pin penetration into the white face.
- The overall assembly height is unchanged.

This is an experimental geometry preview, not an optical simulation or a
print-approved design. Some support-angle limits still need refinement. The
viewer never connects to a printer or an LED controller.

## Static hosting

The site in `docs/` has no backend. Geometry is loaded on demand; the largest
3D download is approximately 45 MiB. Three.js r169 and OrbitControls are served
locally with their upstream MIT license. `docs/manifest.json` records asset
hashes and `docs/version.json` identifies the published snapshot.

The repository was initialized with only the visualizer and its checks.
It contains no private CAD-project history, photos, slicer profiles, device
settings, credentials or generated print files.

## Validate

```sh
python tools/check_visualizer_site.py
cd tools/visualizer-tests
npm install --ignore-scripts
npx playwright install --with-deps chromium
npm test
```

The browser checks exercise every layout, X6/X9, 2D/3D controls, body/mating
views, project-relative URLs, mobile width and visible download failures.

The included GitHub Actions workflow validates and deploys `docs/` to Pages.
Actions are pinned to official release commits; Playwright is pinned exactly.

To package a future locally generated preview snapshot:

```sh
python tools/build_visualizer_site.py --source /path/to/generated/previews
```

Packaging preserves the geometry and strips absolute local paths from public
metadata. The private geometry-generation project is not required to view or
validate this committed static snapshot.
