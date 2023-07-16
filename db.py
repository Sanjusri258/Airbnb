from bson import ObjectId
import pymongo

dbClient = pymongo.MongoClient('mongodb://localhost:27017/')
db = dbClient["Airbnb"]

hosts = db['Hosts']
admins = db['Admins']
categories = db['Categories']
countries = db['Countries']
properties = db['Properties']
users = db['Users']
bookings = db['Bookings']
payments = db['Payments']
ratings = db['Ratings']

def getCountryById(id):
    return countries.find_one({"_id":ObjectId(id)})

def getUserById(id):
    return users.find_one({"_id":ObjectId(id)})


def getRatingsByPropertyId(property_id):
    prp_ratings = ratings.aggregate([
        {"$match": {"property_id": ObjectId(property_id)}},
        {
            "$group": {
                "_id": "null",
                "totalRatings": {"$sum": "$rating"},
                "count": {"$sum": 1}
            }
        }
    ])
    prp_ratings = list(prp_ratings)
    if prp_ratings:
        propertyRating = round(int(prp_ratings[0]['totalRatings']) / int(prp_ratings[0]['count']),1)
        return {'propertyRating': propertyRating, 'count': prp_ratings[0]['count']}
    else:
        return {'propertyRating': 0, 'count': 0}