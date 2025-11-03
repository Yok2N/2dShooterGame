# Top-down Bomber Prototype

This repository contains a small prototype top-down, pixel-art-style bomber game with a simple authoritative server and a client. It's a starting point for the features you requested (attacking/defending teams, planting/defusing, rounds, class selection). The implementation is intentionally minimal so it's easy to extend.

## Requirements

- Python 3.8+
- pygame

Install dependencies (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
```

## Run

- Host (server + local client):

```powershell
python main.py --host
```

- Connect as client to an existing host (replace HOST with server IP):

```powershell
python main.py --connect HOST
```

- Local single-player test (no networking):

```powershell
python main.py
```

## Controls

- Move: WASD or arrow keys
- Action (plant/defuse when near site): Space
- Switch class (local/client only): 1 (melee), 2 (gun), 3 (wizard)


## Notes & current features

- The server is authoritative and broadcasts simple JSON state snapshots.
- Implemented in this iteration:
- Implemented in this iteration:
  - Side switching after round 7 (teams swap roles)
  - Basic bots to fill teams when there are too few players
  - Client-side smoothing (basic linear interpolation)
  - Pre-join lobby UI for choosing name and class
  - Tilemap and simple collision (procedural map)
  - Procedural blocky pixel sprites for classes
  - Combat: gun bullets, wizard projectiles, melee dash
  - Basic client-side prediction & reconciliation using input sequences
  - Simple persistent local matchmaking: hosts register in `lobby.json` for discovery

Missing/To improve:
- Polished tilemap and custom pixel-art sprites (there is a small blocky placeholder renderer)
- Robust network reliability, interpolation/prediction, and latency compensation (we have basic smoothing and prediction; more work possible)
- Matchmaking, NAT traversal, or a public lobby server (this prototype uses a simple local `lobby.json` registry)

Note about matchmaking/NAT traversal:
- This prototype includes a simple local registry file `lobby.json` that hosts write to. It's a basic persistent server browser for local testing only. Full NAT traversal or a public matchmaking server requires additional infrastructure and is outside this prototype; I can help scaffold a simple central lobby service if you want.

## Next steps I can take (pick one or more)
- Improve interpolation with prediction and reconciliation.
- Replace placeholders with proper 8-bit sprites and a tilemap to match an early-Pokémon look.
- Add buying/round economy and per-class weapons/abilities.
- Add more advanced bots (combat, flanking) or a local 5v5 test harness.

