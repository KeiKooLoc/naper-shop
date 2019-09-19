from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['naper_shop']

orders_table = db["orders"]
products_table = db["products"]
