from flask import (Blueprint,
                   render_template)
from flask_login import login_required, current_user


bp = Blueprint("charts", __name__)


@bp.route("/performance_breakdown", methods=("GET", "POST"))
@login_required
def chart_breakdown():

    return render_template("charts/performance_breakdown.html")
