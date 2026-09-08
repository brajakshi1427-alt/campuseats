from flask import jsonify
def problem(error_type, title, status, detail):
    return jsonify({
        "type": error_type,
        "title": title,
        "status": status,
        "detail": detail
    }), statu
