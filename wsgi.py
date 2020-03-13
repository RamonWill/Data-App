from Prescient import app, db
from Prescient import models


@app.shell_context_processor
def make_shell_context():
    return {"db": db,
            "User": models.User,
            "Watchlist": models.WatchlistItems,
            "Groups": models.Watchlist_Group,
            "sectors": models.Sector_Definitions}
