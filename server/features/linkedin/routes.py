"""LinkedIn routes - only routing, no business logic"""
from flask import Blueprint, jsonify
from .controller import LinkedInController

linkedin_blueprint = Blueprint("linkedin", __name__, url_prefix="/api/linkedin")


@linkedin_blueprint.route("/post", methods=["POST"])
def create_post():
    result, status = LinkedInController.create_post()
    return jsonify(result), status


@linkedin_blueprint.route("/post", methods=["DELETE"])
def delete_post():
    result, status = LinkedInController.delete_post()
    return jsonify(result), status


@linkedin_blueprint.route("/profile-analytics")
def get_profile_analytics():
    result, status = LinkedInController.get_profile_analytics()
    return jsonify(result), status


@linkedin_blueprint.route("/post-analytics")
def get_post_analytics():
    result, status = LinkedInController.get_post_analytics()
    return jsonify(result), status


@linkedin_blueprint.route("/posts")
def get_posts():
    result, status = LinkedInController.get_posts()
    return jsonify(result), status


@linkedin_blueprint.route("/post/<path:post_id>/analytics")
def get_post_analytics_by_id(post_id):
    result, status = LinkedInController.get_post_analytics_by_id(post_id)
    return jsonify(result), status
