# WUNSCE Main Website Architecture

```text
Visitor
  │
  ▼
WUNSCE Main Website
  │
  ├── Services
  ├── About
  ├── Contact
  └── Projects
       ├── ESCULAPIO ──> external/live deployment
       ├── NANA ───────> external/live deployment
       ├── FREY ───────> external/live deployment
       ├── TIKAL ──────> external/live deployment
       └── DARWIN ─────> external/live deployment
```

Project links are controlled with environment variables so the main website can be deployed before the individual products are live.
