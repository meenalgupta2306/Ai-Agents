"""OAuth routes - only routing, no business logic"""
from flask import Blueprint, jsonify
from .controller import OAuthController

oauth_blueprint = Blueprint("oauth", __name__, url_prefix="/api/oauth")


@oauth_blueprint.route("/linkedin/init", methods=["GET"])
def linkedin_oauth_init():
    controller = OAuthController()
    result, status = controller.linkedin_oauth_init()
    return jsonify(result), status


@oauth_blueprint.route("/linkedin/finalize", methods=["POST"])
def linkedin_oauth_finalize():
    controller = OAuthController()
    result, status = controller.linkedin_oauth_finalize()
    return jsonify(result), status


@oauth_blueprint.route("/linkedin/connect-accounts", methods=["POST"])
def connect_linkedin_accounts():
    controller = OAuthController()
    result, status = controller.connect_linkedin_accounts()
    return jsonify(result), status


@oauth_blueprint.route("/meta/init", methods=["GET"])
def meta_oauth_init():
    controller = OAuthController()
    result, status = controller.meta_oauth_init()
    return jsonify(result), status


@oauth_blueprint.route("/meta/finalize", methods=["POST"])
def meta_oauth_finalize():
    controller = OAuthController()
    result, status = controller.meta_oauth_finalize()
    return jsonify(result), status


@oauth_blueprint.route("/meta/connect-accounts", methods=["POST"])
def connect_meta_accounts():
    controller = OAuthController()
    result, status = controller.connect_meta_accounts()
    return jsonify(result), status


@oauth_blueprint.route("/connected-accounts", methods=["GET"])
def get_connected_accounts():
    controller = OAuthController()
    result, status = controller.get_connected_accounts()
    return jsonify(result), status


@oauth_blueprint.route("/connected-accounts/<platform>/<path:account_id>", methods=["DELETE"])
def delete_connected_account(platform, account_id):
    controller = OAuthController()
    result, status = controller.delete_connected_account(platform, account_id)
    return jsonify(result), status


@oauth_blueprint.route("/userinfo")
def get_userinfo():
    controller = OAuthController()
    result, status = controller.get_userinfo()
    return jsonify(result) if isinstance(result, dict) else result, status
