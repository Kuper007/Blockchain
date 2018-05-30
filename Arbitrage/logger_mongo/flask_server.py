from flask import Flask, request
from logger_mongo import run_logger
from multiprocessing import Process
import time
import json
import logging
import pymongo


app = Flask(__name__)


# If top > col.count() or top = 0 then col.count() documents will be returned


@app.route('/', methods=['GET'])
def hello_world():
    if "pair" not in request.args:
        return app.response_class(
            response=json.dumps({"error": "Mandatory parameter 'pair' is absent"}),
            status=400,
            mimetype="application/json"
        )
    col_name = "log_" + request.args["pair"]
    if col_name not in col_names:
        return app.response_class(
            response=json.dumps({"error": 'Not supported currency pair'}),
            status=400,
            mimetype="application/json"
        )


    if "top" not in request.args:
        top = 1
    else:
        try:
            top = int(request.args["top"])
        except ValueError:
            return app.response_class(
                response=json.dumps({"error": "Parameter 'top' must be non-negative integer"}),
                status=400,
                mimetype="application/json"
            )
    if top < 0 or top > 100:
        return app.response_class(
            response=json.dumps({"error": "Parameter 'top' must be between 0 and 100"}),
            status=400,
            mimetype="application/json"
        )


    col = db[col_name]
    try:
        return app.response_class(
            response=json.dumps(list(col.find(
                        projection={"_id": False},
                        limit=top,
                        sort=[("_id", pymongo.DESCENDING)])
            )),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        print(type(e))
        print()
        print(e)
        return app.response_class(
            response=json.dumps({"error": "Some problems with database occurred"}),
            status=500,
            mimetype="application/json"
        )


if __name__ == '__main__':
    client = pymongo.MongoClient("mongodb://admin:415096396771@23.100.25.146/admin")  # defaults to port 27017
    db = client["test_db"]
    col_names = set(db.collection_names())

    # Logging
    trading_symbols = ['bch_btc', 'bch_usd', 'dash_btc', 'eth_btc', 'btc_usd', 'xrp_btc', 'dash_usd', 'eth_usd', 'xrp_usd']
    limit = 50
    config_file = 'orders_config.json'
    for symbol in trading_symbols:
        p = Process(target=run_logger, args=(symbol, limit, config_file, db))
        p.start()

    logger = logging.getLogger('werkzeug')
    handler = logging.FileHandler('access.log')
    logger.addHandler(handler)
    app.logger.addHandler(handler)

    # Starting server
    app.run(host='0.0.0.0')