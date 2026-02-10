"""Meta Marketing API Routes"""
from flask import Blueprint, jsonify
from .controller import MetaController

meta_blueprint = Blueprint("meta", __name__, url_prefix="/api/meta")


@meta_blueprint.route("/campaigns", methods=["POST"])
def create_campaign():
    """Create a new Meta campaign"""
    controller = MetaController()
    result, status = controller.create_campaign()
    return jsonify(result), status


@meta_blueprint.route("/campaigns", methods=["GET"])
def get_campaigns():
    """Get campaigns for a Meta ad account"""
    controller = MetaController()
    result, status = controller.get_campaigns()
    return jsonify(result), status
