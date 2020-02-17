from Prescient import app, db
from Prescient import models


@app.shell_context_processor
def make_shell_context():
    return {"db":db, "User":User, "Watchlist":Watchlist}
