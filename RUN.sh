#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed. Install the LTS version from https://nodejs.org/"; exit 1
fi
[ -d node_modules ] || npm install
node setup-env.js
npm start
