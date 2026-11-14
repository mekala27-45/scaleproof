# Public policy verification

The prepared Vercel project is scaleproof-api. The dedicated Neon database is scaleproof with schema scaleproof and the restricted scaleproof_app role. Administrative migration paths are not exposed by the API.

Pending approval: put the restricted connection credential into encrypted DATABASE_URL in Vercel preview and production. Never print it or include it in source, browser code or evidence. Set SCALEPROOF_MODE=live, ALLOWED_ORIGIN=https://mekala27-45.github.io and the exact SOURCE_REVISION.

After deployment, a fresh ordinary client must create a session, create one accepted and one rejected plan, read each receipt, replay the identical request and receive a conflict for changed input under the same key. A separate SQL read must match the exact receipt ID, digest, mode and source revision. Repeat the browser flow without administrative cookies.

Check process-death recovery and concurrent replay against PostgreSQL, not only the SQLite contract fixture. Do not mark gate 09 complete before all three surfaces agree. Do not disable deployment protection to make a check appear public.
