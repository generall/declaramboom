from pymongo import MongoClient
mongo = MongoClient()
db = mongo.declarator

# Fuck mongo
mean_sqrs = db.declarations.aggregate([
    {
        "$project": {
            "square": "$real_estates.square",
            "type": "$real_estates.type.name"
        }
    },
    {
        "$project": {
            "zipped": {
                "$zip": {
                    "inputs": [
                        "$square",
                        "$type"
                    ]
                }
            }
        }
    },
    {
        "$unwind": "$zipped"
    },
    {
        "$project": {
            "square": {
                "$arrayElemAt": [
                    "$zipped",0
                ]
            },
            "type": {
                "$arrayElemAt": [
                    "$zipped",1
                ]
            }
        }
    },
    {
        "$sort": {
            "square": 1
        }
    },
    {
        "$match": {
            "square": {
                "$ne": None
            }
        }
    },
    {
        "$group": {
            "_id": "$type",
            "allSquares": {
                "$push": "$square"
            }
        }
    },
    {
        "$project": {
            "_id": 1,
            "allSquares": 1,
            "num": {
                "$size": "$allSquares"
            }
        }
    },
    {
        "$project": {
            "_id": 1,
            "mean": {
                "$arrayElemAt": [
                    "$allSquares",
                    {
                        "$trunc": {
                            "$divide": [
                                "$num",
                                2
                            ]
                        }
                    }
                ]
            }
        }
    }
], allowDiskUse=True)