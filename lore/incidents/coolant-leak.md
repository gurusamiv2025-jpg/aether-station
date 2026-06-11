# Incident Report: LiF-B Coolant Loop Failure (2096-02-14)

**Classification:** Open. Reactor B remains offline pending parts.

At 03:18 station time on 2096-02-14, the LiF-B coolant loop on Reactor B
lost pressure across a manifold weld in compartment 4-C. Mira-7's automated
isolation routine engaged at 03:18:23 — eleven seconds after pressure
crossed the cutoff threshold — by which time Volkov had already manually
sealed the loop from the engineering panel.

## Sequence

- 03:17:54 — manifold weld fails, slow leak begins
- 03:18:12 — pressure crosses isolation threshold
- 03:18:18 — Volkov, woken by sleep-cycle anomaly alarm, reaches engineering
- 03:18:21 — Volkov initiates manual isolation
- 03:18:23 — Mira-7 issues automated isolation command (redundant)
- 03:18:30 — Park reaches command, declares minor casualty

## Outcome

No injuries. ~140L of LiF coolant lost. Reactor B safed and offline. Station
operating on Reactor A with reduced science load. Replacement manifold and
coolant on the next supply manifest, ETA Q4 2096.

## Why Mira was late

Post-incident review identified a 9-second debounce window in Mira-7's
threshold sensor that, combined with a brief sensor dropout at 03:18:14,
delayed the isolation command. Debounce was reduced to 2 seconds the
following day. Volkov has not let this go.
