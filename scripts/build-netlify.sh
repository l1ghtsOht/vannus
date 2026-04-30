#!/usr/bin/env bash
# NOTE: Primary deployment is Railway. This script is retained for reference only.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/praxis/frontend"
SITE="$ROOT/_site"

echo "==> Cleaning _site/"
rm -rf "$SITE"
mkdir -p "$SITE/home-assets" "$SITE/tools-assets" "$SITE/room-app" "$SITE/static"

echo "==> Building home app"
cd "$FRONTEND/home" && npm ci && npm run build
cp -r "$FRONTEND/home/dist/"* "$SITE/home-assets/"

echo "==> Building tools app"
cd "$FRONTEND/tools" && npm ci && npm run build
cp -r "$FRONTEND/tools/dist/"* "$SITE/tools-assets/"

echo "==> Building room app"
cd "$FRONTEND/room" && npm ci && npm run build
cp -r "$FRONTEND/room/dist/"* "$SITE/room-app/"

echo "==> Copying static HTML pages"
for f in "$FRONTEND"/*.html "$FRONTEND"/*.js; do
  [ -f "$f" ] && cp "$f" "$SITE/static/"
done

echo "==> Copying SEO files"
cp "$FRONTEND/robots.txt" "$SITE/robots.txt"
cp "$FRONTEND/sitemap.xml" "$SITE/sitemap.xml"

echo "==> Copying home index as site root"
cp "$FRONTEND/home/dist/index.html" "$SITE/index.html"

API_URL="${API_BACKEND_URL:?Set API_BACKEND_URL env var in Netlify (e.g. https://vannus-api.up.railway.app)}"

echo "==> Writing _redirects (API → $API_URL)"
cat > "$SITE/_redirects" <<REDIRECTS
# API proxy — forward to Railway backend
/search          ${API_URL}/search          200
/search/*        ${API_URL}/search/:splat   200
/feedback        ${API_URL}/feedback         200
/feedback/*      ${API_URL}/feedback/:splat  200
/tools/*         ${API_URL}/tools/:splat     200
/categories      ${API_URL}/categories       200
/categories/*    ${API_URL}/categories/:splat 200
/compare         ${API_URL}/compare          200
/compare/*       ${API_URL}/compare/:splat   200
/stack           ${API_URL}/stack             200
/stack/*         ${API_URL}/stack/:splat      200
/suggest         ${API_URL}/suggest           200
/suggest/*       ${API_URL}/suggest/:splat    200
/intelligence/*  ${API_URL}/intelligence/:splat 200
/profile         ${API_URL}/profile           200
/profile/*       ${API_URL}/profile/:splat    200
/rfp/*           ${API_URL}/rfp/:splat        200
/health          ${API_URL}/health            200
/cognitive       ${API_URL}/cognitive         200
/cognitive/*     ${API_URL}/cognitive/:splat   200
/room            ${API_URL}/room              200
/room/*          ${API_URL}/room/:splat       200
/api/*           ${API_URL}/api/:splat        200

# SPA routes — serve the appropriate index.html
/journey         /static/journey.html                      200
/privacy-policy  /static/privacy-policy.html               200
/terms-of-service /static/terms-of-service.html            200
REDIRECTS

echo "==> Build complete. Output in _site/"
