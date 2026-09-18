# Configuration drafts

These TOML files reserve configuration shapes for local, hosted, and private profiles. They parse as TOML but the scaffold CLI does not load or enforce them. They are not finalized configuration contracts.

- local.example.toml: primary local path with no API key.
- hosted.example.toml: optional future hosted free/paid access using an environment credential reference.
- private.example.toml: optional future on-premises endpoint.

Use a *.local.toml filename for private copies; those files are ignored by Git. Do not put real keys in these examples. Model IDs, licensing, capability checks, destination rules, and runtime limits must be verified when the loader/adapters are implemented.
