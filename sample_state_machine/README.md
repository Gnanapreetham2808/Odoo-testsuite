# sample_state_machine

Capability sample for **Odoo 19.0**: a small state machine on a custom model, with tests written
in Odoo's test framework. It contains no client data; all data in it is fictitious.

## What it contains

| Part | Where |
|---|---|
| Transition table (plain Python, does not import Odoo) | `transitions.py` |
| Model `sample.booking` (equipment booking request) | `models/booking.py` |
| Groups, access rights, record rules | `security/` |
| List and form views with workflow buttons | `views/booking_views.xml` |
| One plain HTTP route (not JSON-RPC) | `controllers/main.py` |
| Tests | `tests/` |

### The state machine

Five states: `draft`, `submitted`, `approved`, `done`, `cancelled`.

Seven regular transitions:

| Action | From | To |
|---|---|---|
| submit | draft | submitted |
| approve | submitted | approved |
| reject | submitted | draft |
| complete | approved | done |
| cancel | draft | cancelled |
| cancel | submitted | cancelled |
| cancel | approved | cancelled |

One override: `force_cancel`, from `done` to `cancelled`, for booking managers only. It is kept in
its own table, outside the regular transitions.

Rules worth noting:

- `state` is read-only in the UI and cannot be written directly; it moves only through the
  transition methods. A booking can only be created in `draft`.
- `approve` and `reject` need the manager group. Users see only their own bookings; managers see all.
- The table lives in `transitions.py` so the logic can be tested without Odoo or a database.

### The HTTP route

`GET /sample/booking/<id>/status` is a plain HTTP route (`type='http'`, `auth='user'`). It returns
short JSON. Errors never contain a stack trace: an unknown id and a record the user may not read both
return `404 {"error": "not_found"}` (so ids cannot be probed), and any unexpected error returns
`500 {"error": "server_error"}`, with the details written to the server log only.

## Tests

Tags: `sample_sm` (everything), `sample_sm_plain`, `sample_sm_model`, `sample_sm_http`.

| Test file | Kind | What it checks |
|---|---|---|
| `tests/plain/test_transitions_plain.py` | plain Python | the table: counts, legal moves, illegal moves, override |
| `tests/test_transitions_wrapper.py` | Odoo (`BaseCase`) | the same checks, run by the Odoo test runner |
| `tests/test_booking.py` | `TransactionCase` | every state/action pair, direct writes, dates, access rights, override, record rules |
| `tests/test_booking_http.py` | `HttpCase` | status route: success, 404, other user's record, anonymous, no stack trace on error |

The plain tests and the wrapper share one set of checks, so a tag subset gives the same result
locally and on Odoo.sh.

### Run the plain tests (no Odoo, no database)

```
python3 tests/plain/test_transitions_plain.py
```

Run it by file path. The module's `__init__.py` imports Odoo, so `python -m unittest` on the package
would fail without Odoo installed.

### Run all tests in Odoo (one command)

```
odoo-bin -d <new_db> -i sample_state_machine --test-tags=/sample_state_machine --stop-after-init
```

Run a subset by tag, for example:

```
odoo-bin -d <db> -u sample_state_machine --test-tags=sample_sm_model --stop-after-init
```

The module depends only on `base`, so Odoo Community is enough; the Enterprise source is not needed.

## Design notes

- Fixtures are created in the tests themselves. They do not use Odoo's demo data, so results do not
  change when the Odoo revision is renewed.
- The route is a plain HTTP route so an error response can never show a stack trace.
