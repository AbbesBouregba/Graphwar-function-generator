# Graphwar Function Generator
#### Video Demo:  <https://youtu.be/unQ32-PY7BE?si=rhAhYxQdCvNZWH3S>
## What the project does
 
Graphwar is a game where you and your team are points on the negative-x side of an orthonormal plane (O, i, j) spanning `[-25,25] x [-15,15]`, facing opponents on the positive side. You win by writing a function `y = f(x)` that, when drawn by the game's graphing calculator (with a Y-offset depending on your own Y-coordinate visit https://www.graphwar.com/tutorial.html for more info ), passes through the opponents' positions and eliminates them. Last team standing wins.
 
After studying interpolation in numerical analysis class, it clicked: interpolation is — in theory — the perfect tool to pass through every opponent's point and one-shot the whole team. This project is the result of chasing that idea through three increasingly better approaches.

## How it works
 
**Coordinate capture.** Opponent positions come from mouse clicks, converted from screen pixels into Graphwar's `(x, y)` system via an affine transform, calibrated once per screen and cached to CSV:
 
$$x_{game} = (x_{px} - x_{0,px}) \cdot \frac{25}{w_{px}}, \qquad y_{game} = -\frac{15}{h_{px}}\,(y_{px} - y_{0,px})$$


Getting `x_{0,px}`, `y_{0,px}`, `w_{px}` and `h_{px}` (`a1`, `a2`, `b1`, `b2` in the code) means anchoring the pixel grid to two known in-game points. `callibre()` asks you to click on `(25, 0)` and `(0, 15)` inside an actual Graphwar match — two points on the axes whose in-game coordinates are known ahead of time — then derives the origin's pixel position and the pixel span per game unit from the difference between those two clicks. That's cheaper than deriving the transform from screen resolution and window position, and it self-corrects for whatever zoom level or window size the game happens to be running at. The result is written to `calibre.csv` so the ritual only has to happen once per screen, not once per match; `load_calibre()` just reads it back in on subsequent runs.

Both calibration and target capture reuse the same primitive, `get_n_clicks(n)`: a `pynput` mouse listener that blocks until `n` clicks land, echoing each one back so you can confirm it registered the right spot.
 
**Method 1 — Lagrange interpolation.** The first attempt: a Lagrange polynomial through every clicked point, named `interpolation` (simplest to implement compared to Newton's form or cubic splines). Tested on GeoGebra, essentially perfect. In-game, far more limited — obstacles aside, **Runge's phenomenon** kicks in: a Lagrange polynomial starts oscillating sharply between points once they're close together and numerous, i.e. once the degree gets high.
 
| Degree | Reliability |
|---|---|
| 1st–2nd | Nearly perfect |
| 3rd | Good, most of the time |
| 4th | Doable, with some luck |
| 5th+ | Not viable |
 
`interpolation` itself only computes the math — a list of terms, each holding the `x_j` values the term subtracts and its precomputed coefficient. Turning that into something Graphwar's function box can actually read is `written_polynomial`'s job: it walks that list and stitches together the literal string `(coeff)*(x-x_j)*(x-x_k)*...`, joined with `+` across terms, then cleans up the stray `--` that show up whenever a coefficient or an `x_j` is itself negative (Python string-formats the sign in place rather than simplifying it). Coefficients that are extremely small or large get routed through the scientific-notation formatter below rather than printed in Python's default float form, since Graphwar's parser doesn't tolerate `1.2e-05`-style notation.
 
**Method 2 — Gaussian sum.** A Gaussian bell curve behaves like a Dirac spike when its variable is parameterized tightly enough — so instead of one high-degree polynomial, sum a compressed bell curve per target.
 
Graphwar's characters are `D = 1` unit wide, so a curve within `±0.5` of a target still hits it. For a target `(x₀, y₀)` and offset `c`:
 
$$\forall x \in [0,25], \quad (x - x_0)^2 + \big(f(x) + c - y_0\big)^2 \le 0.25 \implies \text{enemy is hit}$$
 
The `gaussian` function, for target point `i+1`:
 
$$g_i(x) = \big(y_{i+1} - y_0\big)\, e^{-\left(10\,(x - x_{i+1})\right)^2}$$
 
With `k = 10`, this beat interpolation outright — on an empty map, essentially exact regardless of target count. Its one weakness: it still assumes a clear path.
 
**Method 3 — Sigmoid sum.** That clear-path assumption falls apart on most real Graphwar maps — they're rarely obstacle-free, if anything the opposite. That called for a different way of thinking about the curve entirely.
 
Interpolation, when it works, moves smoothly — but that same freedom becomes a liability as more points get added: nothing constrains the path between them. Gaussian sum is the opposite: sharp, sudden transitions around each target, then straight back to a stable baseline — which is exactly the problem. What if, instead of returning to normal after hitting a target, the function just stayed there?
 
A sigmoid transitions from one bound to another around `x₀`; `k` sets how abrupt that transition is — small `k` gives a gradual ramp, large `k` collapses it into a near-instant step:
 
$$\sigma(x) = \frac{1}{1 + e^{-k(x-x_0)}}$$
 
Summing several heavily compressed sigmoids, each shifted to a target's x-position, builds a staircase — the function steps up or down to meet each opponent's Y-level and stays there:
 
$$s(x) = y_0 + \sum_i (y_{i+1} - y_i)\, \sigma_i(x)$$
 
Unlike interpolation or Gaussian sum, which ask "where are the enemies," sigmoid sum asks "where do you want to pass through" — the path can be routed around obstacles instead of just aimed at targets. It's the first method to actually address obstacle avoidance, and by far the strongest of the three.
 
**Bonus — scientific notation formatter.** A small helper function to work around Python's default (unreadable) representation of very small or very large floats, used for cleanly printing/generating the function strings above.
 
## File-by-file breakdown
 
| File | Contains | Role |
|---|---|---|
| `project.py` | `main`, `get_n_clicks`, `callibre`, `load_calibre`, `interpolation`, `written_polynomial`, `gaussian`, `sigmoids_sum`, `to_sci_str` | All project code — coordinate capture, calibration, the three curve-generation methods, and the program's entry point (`main`) |
| `test_project.py` | `test_interpolation`, `test_written_polynomial`, `test_gaussian`, `test_sigmoids_sum`, `test_to_sci_str` | Unit tests for each importable function in `project.py` (excluding `main`, and functions relying on live mouse/keyboard input) |
| `calibre.csv` | Cached calibration values (`a1`, `a2`, `b1`, `b2`) | Generated by `callibre()` and read back by `load_calibre()`; not code, just cached per-screen calibration data |
| `requirements.txt` | `pynput`, etc. | Project dependencies |
| `README.md` | — | This document |
 
## How to play
 
1. **Run the program**, and calibrate first (option 2) if you haven't already on this screen — click `(25, 0)` then `(0, 15)` in an actual Graphwar match, as precisely as you can.
2. **Pick game mode** (option 1) and enter how many points you want your function to pass through, *not counting your own point* — your character is always the first click and gets added automatically.
3. **ALT+TAB into Graphwar** and start clicking: your character's point first, then the points you want to pass through, **in increasing X-coordinate order**. Only click enemy positions after you've clicked your own.
4. **Pick whichever method's output fits the fight**:
   - **Lagrange polynomial** — best with 4 or fewer targets, reasonably spaced, and not much in the way; push past that and Runge's phenomenon takes over.
   - **Gaussian sum** — handles any number of targets as long as the path to them is clear; an obstacle beats it regardless of point count.
   - **Sigmoid sum** — the strongest of the three by far, and the one to reach for by default. Click every point you want the curve to actually pass through, in increasing X order, to steer it around obstacles instead of just aiming at targets — X-axis ordering matters here even more than for the other two, since the staircase is built step by step in that order.
5. **Copy the printed function** for whichever method you chose into Graphwar's function input box.
 
## Design choices and trade-offs
 
- **Manual point-clicking over computer-vision auto-detection.** Simpler and more reliable to implement first; auto-detecting opponents is future work.
- **Lagrange over Newton/cubic splines** for the first method — algorithmically the simplest, despite Newton and splines being more numerically robust; the plan was always to move past pure interpolation anyway once Runge's phenomenon showed up.
- **`k = 10` for the Gaussian sum** — a deliberate safety margin. A Gaussian bump must rise and fall within the domain, so too steep a `k` risks the peak slipping between two sample points and missing the target Y-value entirely.
- **High `k` for the sigmoid sum**, by contrast, is safe to push hard — a sigmoid is monotonic, so steepness sharpens the staircase without threatening correctness the way it would for a Gaussian.
- **Sigmoid sum over Gaussian sum as the default**, despite Gaussian being marginally more accurate on obstacle-free maps, because most real maps aren't obstacle-free — obstacle avoidance mattered more than peak precision.
## Why this project
 
The goal, beyond winning at Graphwar, was to share an interest in math — numerical analysis specifically. You don't need math to be a good programmer, but skipping it means missing out on projects like this one.
