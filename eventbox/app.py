"""EventBox: the whole web app. create_app builds the app and every route is in register_routes.

The business rules live in the modules next to this file (catalog, orders, pricing, inventory,
...): a route reads the request, calls them and shows the result.
"""

from flask import Flask, abort, flash, redirect, render_template, request, session

from eventbox import (
    auth,
    catalog,
    checkin,
    db,
    describe,
    emails,
    money,
    orders,
    qr,
    refunds,
    settings,
    site,
    timeutil,
)


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE="eventbox.sqlite",
        SECRET_KEY=settings.SECRET_KEY,
        DOOR_KEY=settings.DOOR_KEY,
    )
    app.config.update(config or {})
    db.migrate(app.config["DATABASE"])  # runs the new files in eventbox/migrations/, once each
    app.jinja_env.filters["bhd"] = money.bhd  # {{ 15000 | bhd }} shows 15.000 BHD
    app.jinja_env.filters["when"] = timeutil.show  # {{ event.starts_at | when }}
    app.context_processor(site.template_values)  # {{ site.brand }} in every template
    app.context_processor(lambda: {"user": auth.current_user()})
    register_routes(app)
    return app


def json_body():
    """The request's JSON object, or {}."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def register_routes(app):
    # ---------------------------------------------------------------- pages for everyone

    @app.get("/")
    def home():
        conn = db.connect()
        try:
            events = catalog.list_events(conn)[:3]
        finally:
            conn.close()
        return render_template("home.html", events=events)

    @app.get("/events")
    def event_list():
        conn = db.connect()
        try:
            events = catalog.list_events(conn)
        finally:
            conn.close()
        return render_template("events.html", events=events)

    @app.get("/events/<int:event_id>")
    def event_page(event_id):
        conn = db.connect()
        try:
            event = catalog.event_details(conn, event_id)
        finally:
            conn.close()
        if event is None:
            abort(404)
        return render_template("event.html", event=event)

    @app.post("/events/<int:event_id>/buy")
    def buy(event_id):
        """The form on the event page."""
        user = auth.current_user()
        conn = db.connect()
        try:
            try:
                order = orders.place_order(conn, event_id, request.form.to_dict(), user)
            except orders.OrderError as exc:
                event = catalog.event_details(conn, event_id)
                if event is None:
                    abort(404)
                return render_template("event.html", event=event, error=exc.message), exc.status
        finally:
            conn.close()
        return redirect(f"/orders/{orders.code_of(order)}")

    @app.get("/orders/<code>")
    def order_page(code):
        conn = db.connect()
        try:
            order = orders.find_order(conn, code)
            if order is None:
                abort(404)
            event = catalog.find_event(conn, order["event_id"])
            tokens = orders.tickets_of(conn, order)
        finally:
            conn.close()
        return render_template(
            "order.html", order=order, code=orders.code_of(order), event=event, tokens=tokens
        )

    @app.get("/orders/<code>/email")
    def order_email(code):
        """The confirmation email in the browser ("Can't see this email? Open it here")."""
        conn = db.connect()
        try:
            order = orders.find_order(conn, code)
            if order is None:
                abort(404)
            event = catalog.find_event(conn, order["event_id"])
            subject, body = emails.confirmation(order, event, orders.tickets_of(conn, order))
        finally:
            conn.close()
        return render_template("email.html", subject=subject, lines=body.split("\n"))

    @app.post("/orders/<code>/refund")
    def refund_form(code):
        conn = db.connect()
        try:
            order = orders.find_order(conn, code)
            if order is None:
                abort(404)
            try:
                amount = refunds.refund(conn, order)
            except refunds.RefundError as exc:
                flash(f"No refund: {exc.message}.")
            else:
                flash(f"Refunded: {money.bhd(amount)}.")
        finally:
            conn.close()
        return redirect(f"/orders/{code}")

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/help")
    def help_page():
        return render_template("help.html")

    @app.get("/healthz")
    def health():
        return {"ok": True}

    # ---------------------------------------------------------------- accounts

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            conn = db.connect()
            try:
                user = auth.check_login(
                    conn, request.form.get("email"), request.form.get("password")
                )
            finally:
                conn.close()
            if user is not None:
                auth.log_in(user)
                target = request.args.get("next", "")
                # Only our own pages: "//evil.example" would leave the site.
                if not target.startswith("/") or target.startswith("//"):
                    target = "/organiser" if user["role"] == "organiser" else "/account"
                return redirect(target)
            error = "Wrong email or password."
        return render_template("login.html", error=error), 401 if error else 200

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect("/")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        error = None
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            name = (request.form.get("name") or "").strip()
            password = request.form.get("password") or ""
            if "@" not in email or not name:
                error = "Enter your name and your email."
            elif len(password) < 8:
                error = "Choose a password of 8 characters or more."
            else:
                conn = db.connect()
                try:
                    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
                        error = "That email already has an account: log in instead."
                    else:
                        cursor = conn.execute(
                            "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                            (email, name, auth.hash_password(password)),
                        )
                        conn.commit()
                        user = conn.execute(
                            "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
                        ).fetchone()
                        auth.log_in(user)
                        return redirect("/account")
                finally:
                    conn.close()
        return render_template("signup.html", error=error), 400 if error else 200

    @app.get("/login/facebook")
    def facebook_login():
        return redirect(auth.facebook_login_url())

    @app.get("/login/facebook/callback")
    def facebook_callback():
        conn = db.connect()
        try:
            user = auth.facebook_user(conn, request.args.get("code"), request.args.get("state"))
        except auth.FacebookError as exc:
            return render_template("login.html", error=f"Facebook login failed: {exc}."), 502
        finally:
            conn.close()
        auth.log_in(user)
        return redirect("/account")

    @app.get("/account")
    @auth.login_required
    def account():
        user = auth.current_user()
        conn = db.connect()
        try:
            rows = conn.execute(
                "SELECT orders.*, events.name AS event_name, events.starts_at FROM orders"
                " JOIN events ON events.id = orders.event_id"
                " WHERE orders.user_id = ? OR orders.email = ? ORDER BY orders.id DESC",
                (user["id"], user["email"]),
            ).fetchall()
        finally:
            conn.close()
        return render_template("account.html", orders=rows, code_of=orders.code_of)

    # ---------------------------------------------------------------- organisers

    @app.get("/organiser")
    @auth.organiser_required
    def organiser_home():
        user = auth.current_user()
        conn = db.connect()
        try:
            rows = conn.execute(
                "SELECT events.*, COALESCE(SUM(orders.quantity), 0) AS sold,"
                " COALESCE(SUM(orders.total_fils), 0) AS revenue FROM events"
                " LEFT JOIN orders ON orders.event_id = events.id AND orders.status = 'paid'"
                " WHERE events.organiser_id = ? GROUP BY events.id ORDER BY events.starts_at",
                (user["id"],),
            ).fetchall()
        finally:
            conn.close()
        return render_template("organiser.html", events=rows)

    def read_event_form(form):
        """(fields, error) of the new / edit event form."""
        name = (form.get("name") or "").strip()
        venue = (form.get("venue") or "").strip()
        starts_at = (form.get("starts_at") or "").strip().replace("T", " ")
        try:
            timeutil.parse(starts_at)
        except ValueError:
            return None, "Write the start like 2026-12-31 18:00 (UTC)."
        price = (form.get("price") or "0").strip()
        whole, _, decimals = price.partition(".")
        if not whole.isdigit() or (decimals and not decimals.isdigit()) or len(decimals) > 3:
            return None, "Write the price in BHD, like 12.500."
        price_fils = int(whole) * 1000 + int((decimals or "0").ljust(3, "0"))
        capacity = (form.get("capacity") or "").strip()
        if not capacity.isdigit() or int(capacity) < 1:
            return None, "The capacity is a whole number of 1 or more."
        if not name or not venue:
            return None, "Every event needs a name and a venue."
        fields = {
            "name": name,
            "venue": venue,
            "starts_at": starts_at,
            "price_fils": price_fils,
            "capacity": int(capacity),
            "description": (form.get("description") or "").strip(),
        }
        return fields, None

    @app.route("/organiser/events/new", methods=["GET", "POST"])
    @auth.organiser_required
    def new_event():
        error = None
        if request.method == "POST":
            fields, error = read_event_form(request.form)
            if fields is not None:
                conn = db.connect()
                try:
                    cursor = conn.execute(
                        "INSERT INTO events (name, venue, starts_at, price_fils, capacity,"
                        " description, organiser_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (*fields.values(), auth.current_user()["id"]),
                    )
                    conn.commit()
                finally:
                    conn.close()
                return redirect(f"/organiser/events/{cursor.lastrowid}/edit")
        return render_template("event_form.html", event=None, error=error), 400 if error else 200

    def own_event(conn, event_id):
        """The organiser's own event, or 404 (another organiser's event looks unknown)."""
        event = catalog.find_event(conn, event_id)
        if event is None or event["organiser_id"] != auth.current_user()["id"]:
            abort(404)
        return event

    @app.route("/organiser/events/<int:event_id>/edit", methods=["GET", "POST"])
    @auth.organiser_required
    def edit_event(event_id):
        error = None
        conn = db.connect()
        try:
            event = own_event(conn, event_id)
            if request.method == "POST":
                fields, error = read_event_form(request.form)
                if fields is not None:
                    conn.execute(
                        "UPDATE events SET name = ?, venue = ?, starts_at = ?, price_fils = ?,"
                        " capacity = ?, description = ? WHERE id = ?",
                        (*fields.values(), event_id),
                    )
                    conn.commit()
                    flash("Saved.")
                    return redirect(f"/organiser/events/{event_id}/edit")
        finally:
            conn.close()
        return render_template("event_form.html", event=event, error=error), 400 if error else 200

    @app.post("/organiser/events/<int:event_id>/description")
    @auth.organiser_required
    def describe_form(event_id):
        """The Write it for me button on the edit page."""
        conn = db.connect()
        try:
            event = own_event(conn, event_id)
            describe.write_description(conn, event, request.form.get("notes", ""))
        finally:
            conn.close()
        flash("The AI wrote a new description.")
        return redirect(f"/organiser/events/{event_id}/edit")

    @app.get("/organiser/events/<int:event_id>/attendees")
    @auth.organiser_required
    def attendees(event_id):
        conn = db.connect()
        try:
            event = own_event(conn, event_id)
            rows = conn.execute(
                "SELECT * FROM orders WHERE event_id = ? AND status = 'paid' ORDER BY id",
                (event_id,),
            ).fetchall()
        finally:
            conn.close()
        return render_template("attendees.html", event=event, orders=rows, code_of=orders.code_of)

    # ---------------------------------------------------------------- the JSON API

    @app.get("/api/events")
    def api_events():
        conn = db.connect()
        try:
            events = catalog.list_events(conn)
        finally:
            conn.close()
        return {"events": [{k: v for k, v in e.items() if k != "when"} for e in events]}

    @app.get("/api/events/<int:event_id>")
    def api_event(event_id):
        conn = db.connect()
        try:
            event = catalog.event_details(conn, event_id)
        finally:
            conn.close()
        if event is None:
            return {"error": "event not found"}, 404
        prices = [{"name": name, "price_fils": fils} for name, fils in event["prices"]]
        return {**{k: v for k, v in event.items() if k != "when"}, "prices": prices}

    @app.post("/api/events/<int:event_id>/orders")
    def api_buy(event_id):
        conn = db.connect()
        try:
            order = orders.place_order(conn, event_id, json_body(), auth.current_user())
            body = orders.order_json(conn, order)
        except orders.OrderError as exc:
            return {"error": exc.message}, exc.status
        finally:
            conn.close()
        return body, 201

    @app.get("/api/orders/<code>")
    def api_order(code):
        conn = db.connect()
        try:
            order = orders.find_order(conn, code)
            body = orders.order_json(conn, order) if order is not None else None
        finally:
            conn.close()
        if body is None:
            return {"error": "order not found"}, 404
        return body

    @app.get("/api/orders/<code>/tickets")
    def api_tickets(code):
        conn = db.connect()
        try:
            order = orders.find_order(conn, code)
            if order is None:
                return {"error": "order not found"}, 404
            rows = conn.execute(
                "SELECT qr, checked_in_at FROM tickets WHERE order_id = ? ORDER BY id",
                (order["id"],),
            ).fetchall()
        finally:
            conn.close()
        tickets = [{"token": r["qr"], "checked_in": r["checked_in_at"] is not None} for r in rows]
        return {"code": orders.code_of(order), "tickets": tickets}

    @app.post("/api/orders/<code>/refund")
    def api_refund(code):
        conn = db.connect()
        try:
            order = orders.find_order(conn, code)
            if order is None:
                return {"error": "order not found"}, 404
            try:
                amount = refunds.refund(conn, order)
            except refunds.RefundError as exc:
                return {"error": exc.message}, exc.status
        finally:
            conn.close()
        return {"code": orders.code_of(order), "status": "refunded", "refund_fils": amount}

    @app.post("/api/tickets/verify")
    def api_verify():
        """Is this QR code one of our tickets? For the organisers' own scanner apps."""
        conn = db.connect()
        try:
            ticket = qr.find_ticket(conn, json_body().get("token"))
        finally:
            conn.close()
        if ticket is None:
            return {"valid": False}, 404
        return {"valid": True, "event": ticket["event_id"]}

    @app.post("/api/checkin")
    def api_checkin():
        conn = db.connect()
        try:
            ticket = checkin.check_in(conn, json_body(), app.config["DOOR_KEY"])
        except checkin.CheckinError as exc:
            return {"error": exc.message}, exc.status
        finally:
            conn.close()
        return {"checked_in": True, "event": ticket["event_id"]}

    @app.post("/api/organiser/events/<int:event_id>/description")
    @auth.organiser_required
    def api_describe(event_id):
        conn = db.connect()
        try:
            event = own_event(conn, event_id)
            notes = json_body().get("notes")
            result = describe.write_description(
                conn, event, notes if isinstance(notes, str) else ""
            )
        finally:
            conn.close()
        return result

    # ---------------------------------------------------------------- errors

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return {"error": "not found"}, 404
        return render_template("404.html"), 404
