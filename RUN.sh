#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -d node_modules ] || npm install
(sleep 4; (xdg-open http://localhost:4000 || open http://localhost:4000) >/dev/null 2>&1) &
node server.js
