"""Chat routes - only routing, no business logic"""
from flask import Blueprint
from .controller import ChatController

chat_blueprint = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_blueprint.route("/sessions", methods=["GET"])
def get_sessions():
    result, status = ChatController.get_sessions()
    from flask import jsonify
    return jsonify(result), status


@chat_blueprint.route("/sessions", methods=["POST"])
def create_session():
    result, status = ChatController.create_session()
    from flask import jsonify
    return jsonify(result), status


@chat_blueprint.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    result, status = ChatController.delete_session(session_id)
    from flask import jsonify
    return jsonify(result), status


@chat_blueprint.route("/sessions/<session_id>/messages", methods=["GET"])
def get_session_messages(session_id):
    result, status = ChatController.get_session_messages(session_id)
    from flask import jsonify
    return jsonify(result), status


@chat_blueprint.route("/message", methods=["POST"])
def send_message():
    result, status = ChatController.send_message()
    from flask import jsonify
    return jsonify(result), status


@chat_blueprint.route("/reports/<filename>", methods=["GET"])
def get_report(filename):
    return ChatController.get_report(filename)


@chat_blueprint.route("/reports/images/<filename>", methods=["GET"])
def get_report_image(filename):
    return ChatController.get_report_image(filename)


@chat_blueprint.route("/reports/charts/<filename>", methods=["GET"])
def get_report_chart(filename):
    return ChatController.get_report_chart(filename)
