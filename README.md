# EventBox

EventBox sells tickets for events all over Bahrain: concerts, comedy, food festivals and talks.
Organisers put their events on the site and scan the tickets at the door. Copperleaf Digital took
the site over from another agency: it works and sells tickets every day, and the client has a
long list of fixes and changes. Read `COMPANY.md` first: it has the client's rules and the house
rules.

## Your tasks
**Your exact task is in Darbni.** Open the task there and read its page: it has the rules and
the values (prices, limits, dates) for YOUR version. Every intern gets their own version, so a
solution copied from someone else will fail the tests.

## Run it
```
python -m venv .venv
.venv\Scripts\activate          # Windows (on macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
flask --app eventbox run --debug
```
Open http://127.0.0.1:5000. The database is `eventbox.sqlite`. Delete it to start over with the
demo data: 9 events, a few orders, a customer (`fatima@example.com`, password `events123`) and an
organiser (`organiser@eventbox.example`, password `stage123`).

Try the API with curl:
```
curl http://127.0.0.1:5000/api/events
curl -X POST http://127.0.0.1:5000/api/events/1/orders -H "Content-Type: application/json" -d "{\"email\": \"sara@example.com\", \"quantity\": 2}"
```

## Test it
```
pytest
```
These tests are yours to run and extend. Darbni runs its own hidden tests on every submission,
each on a new, empty database: whatever your change needs (a table, a column, rows) must be
created by `create_app`, from `eventbox/migrations/`.

## The database
`create_app` runs every NEW file in `eventbox/migrations/`, in name order, once per database
(`eventbox/db.py`). To add a table, a column, an index or rows, add a new file with a higher
number, like `0010_seat_categories.sql`. Never edit a file that already ran.

## Times
Event starts are stored in UTC, and the API answers them in UTC. People read Bahrain time
(Asia/Bahrain, UTC+3): pages and emails show times through `eventbox/timeutil.py`.
"Now" always comes from `eventbox/clock.py` (`clock.now()`, `clock.today()`), never from
`datetime.now()`: tests set the time with the app's `NOW` setting, like `tests/conftest.py`.

## The AI rule
All AI calls go through `eventbox/ai.py`. Always call it like this:
```python
from eventbox import ai

reply = ai.ask_llm(prompt)
```
Not `from eventbox.ai import ask_llm`: Darbni's tests swap `ai.ask_llm` for a fake model, and
that import would keep the real one. `ask_llm` can fail, so always have a fallback. On your
machine `ask_llm` returns a demo reply; set `EVENTBOX_AI=fail` to make it fail.

## Where things are
| File | What it does |
|---|---|
| `eventbox/app.py` | `create_app(config)` and every route (the old agency's one big file) |
| `eventbox/catalog.py` | the events: the list and one event's details |
| `eventbox/orders.py` | buying tickets: `place_order()`, order codes, the order JSON |
| `eventbox/inventory.py` | tickets left, holding them while an order is saved |
| `eventbox/pricing.py` | ticket prices |
| `eventbox/qr.py` | the codes in the tickets' QR codes |
| `eventbox/emails.py` | the confirmation email |
| `eventbox/auth.py` | logging in (email and password, Facebook) |
| `eventbox/refunds.py` | refunds |
| `eventbox/checkin.py` | check-in at the door |
| `eventbox/describe.py` | the AI that writes event descriptions |
| `eventbox/timeutil.py` | how times are shown |
| `eventbox/site.py` | what every page shows about EventBox (`site` in templates) |
| `eventbox/settings.py` | settings and secrets (from the environment on the server) |
| `eventbox/clock.py` | `clock.now()`, `clock.today()`: the only way to read the time |
| `eventbox/money.py` | `bhd(fils)`: `15000` shows as `15.000 BHD` |
| `eventbox/db.py` | `db.connect()` and the migrations |
| `eventbox/migrations/` | the database, one `.sql` file per change |
| `eventbox/ai.py` | `ask_llm(prompt)`, the only way to call AI |
| `eventbox/templates/` | `base.html`, `_event_card.html` (an event in a list) and one template per page |
| `tests/` | pytest tests |
