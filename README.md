# Module 1 Expedition (v0)

Playable Module 1 salvage sortie prototype (Vite + React + TS + Canvas).

Design spec:
- ../module1-spec/MODULE1_SPEC.md
- docs/MODULE1_SPEC.md

## How to run
1. cd module1-expedition
2. npm install
3. npm run dev
4. Open the printed localhost URL

Production build: npm run build then npm run preview

## Controls
- Left click: move leader
- Space: fire nearest in range
- E: salvage / extract
- P: pause
- Wingman panel: stance + waypoint only

## Balance (src/config/balance.ts)
- moveSpeed 80, visionRange 180, weaponRange 140, engageRange 130
- maxOperationTimeSec 180, carrierCapacity 2, ammoStock 28
- Debug panel can tweak speed/vision/range and reveal fog

## Architecture
- Realtime dt sim, continuous XY (no turns/tiles)
- WingmanBrain: src/game/wingman/brain.ts
- Result export: src/game/result.ts (no Module 2 handoff)
- Japanese UI labels in the app

ZIP excludes node_modules and build caches.
