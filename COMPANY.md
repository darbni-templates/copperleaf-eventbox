# Copperleaf Digital

**Copperleaf Digital** is a digital agency: we build web apps for our clients and keep them
running. Every project is a different client's app. Lucia, our product manager, speaks for the
client: when the client changes their mind, the change comes through her.

## The team
| Name | Role | Ask them about |
|---|---|---|
| Adam Clarke | Delivery manager | priorities, deadlines, what the client sees and when |
| Salma Idris | Senior engineer | the code, Flask, SQLite, how to approach a task |
| Kenji Watanabe | QA engineer | how something should behave, edge cases, failing checks |
| Lucia Fernandez | Product manager, the client's voice | what the client asked for and why |
| Mona Jaber | People partner | the internship, your workload, holidays |

## The client: EventBox
**EventBox** sells tickets for events all over Bahrain, for many organisers. The site works and
sells every day, but it grew fast: one big `app.py` with every route, a few bugs that cost money
(sold-out events still sell), and a list of changes the organisers keep asking for. Our job: fix
and change it without stopping the sales.

## What the site does today
- `/events`: the upcoming events, and a page per event with a form to buy tickets.
- Orders as a guest or logged in, an order page with the tickets' QR codes and the confirmation
  email, and `/account` for a customer's orders.
- `/organiser`: the organisers' events, sales, an AI that writes descriptions, the attendees.
- The JSON API for the client's mobile app: `/api/events`, `/api/events/<id>/orders`,
  `/api/orders/<code>`, ticket checks for the door.

## The client's rules
- An event's **capacity** is the number of tickets it can sell; refunded orders give their
  tickets back.
- Event times are stored and sent by the API in **UTC**; people read **Bahrain time**.
- A percentage of a price is rounded half up to the fils.
- An order's code is `EB-` and 1000 + its id: `EB-1015`, ...

The exact paths, texts and numbers of each change are on your task page in Darbni.

## House rules
- Money is stored in **fils** as whole numbers (1 BHD = 1000 fils) and shown as BHD with 3
  decimals: `15.000 BHD`. `money.bhd()` (the `bhd` template filter) does that for you.
- Times are Bahrain time for people (`Asia/Bahrain`). Ask `clock.now()`, never `datetime.now()`.
- The weekend is Friday and Saturday.
- The database changes only through a new file in `eventbox/migrations/`.
- Templates use plain paths (`/events/1`), not `url_for`, except for the stylesheet.
- All code lives in the `eventbox` package. AI only through `eventbox/ai.py`, with a fallback.
- Run `pytest` and try the page in your browser before you submit.
