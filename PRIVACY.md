# ColonyMind demo privacy

The public ColonyMind demo can be tested anonymously. Anonymous browser and
experiment identifiers are random, contain no entered identity, and are held in
bounded server memory; refreshing the page discards anonymous experiment
versions.

Google login is optional. When used, ColonyMind verifies the Google access token
server-side and stores the Google subject identifier, verified email, display
name, profile image URL, and the user's versioned experiment records in the
configured PostgreSQL database. The OpenAI API key is never sent to the browser.

The GPT-5.6 Research Auditor receives only the aggregate snapshot declared in
the interface. It receives no raw retinal pixels, drawings, cell prototypes,
Google access tokens, email addresses, or mutable learning-engine reference, and
requests use `store=false`.

This Build Week demonstration does not sell personal data. A user may request
removal of authenticated experiment records through the repository owner. The
production operator is responsible for server backups and retention after the
judging period.
