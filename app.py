import datetime
import os
import random
import re
from datetime import date, datetime, timedelta

import pymongo
from bson import ObjectId
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)

import db

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static"

app = Flask(__name__)
app.secret_key = "poiuytrewqasdfghjkl"

# admin Views
@app.route("/admin/")
@app.route("/admin/login/", methods=['GET','POST'])
def admin_login():
    error_msg = ""
    if request.method == "POST":
        values = {
            "user_name":request.form.get("user_name"),
            "password":request.form.get("password"),
        }
        
        result = db.admins.find_one(values)
        if result:
            session["logged_in"] = True
            del result["password"]
            session["fullname"] = result["fullname"]
            session["role"] = "Admin"
            return redirect(url_for("admin_home"))
        else:
            error_msg = "Invalid Login Credentials"
            
    return render_template("/admin/login.html", error_msg=error_msg)


@app.route("/admin/home/")
def admin_home():
    hosts = db.hosts.count_documents({"status":True})
    verified_hosts = db.hosts.count_documents({"status":True, "is_verified":True})
    users = db.users.count_documents({"status":True})
    dashboard = {
        "hosts":hosts,
        "users":users,
        "verified_hosts":verified_hosts
    }
    return render_template("/admin/home.html", dashboard=dashboard)

# admin change password
@app.route("/admin/change-password/", methods=['GET','POST'])
def admin_change_password():
    if request.method == "POST":
        values = {
            "password":request.form.get("password"),
        }
        result = db.admins.update_one({},{"$set":values})
        flash("Password Updated successfully","success")
        return redirect(url_for("admin_change_password"))
    
    return render_template("/admin/change-password.html")

@app.route("/admin/categories/")
def admin_categories():
    category = ""
    category_id = request.args.get("category_id")
    # Edit Categories
    if category_id:
        category = db.categories.find_one({"_id":ObjectId(category_id)})

    # get all categories with status true
    categories = db.categories.find({"status":True})
    categories = list(categories)
    list.reverse(categories)
    
    return render_template("/admin/categories.html",category=category, categories=categories)

@app.route("/admin/categories/", methods=['POST'])
def admin_categories_post():
    category_name = request.form.get("category_name")
    category_id = request.form.get("category_id")
    if not category_id:
        # Add Category
        db.categories.insert_one({"category_name":category_name, "status":True})
        flash("Category Added Successfully","success")
    else:
        # Update Category
        db.categories.update_one({"_id":ObjectId(category_id)},{"$set":{"category_name":category_name}})
        flash("Category Updates Successfully","success")

    return redirect(url_for("admin_categories"))

# delete categories
@app.route("/admin/category/delete/<category_id>/", methods=['GET'])
def admin_categories_delete(category_id):
    category = db.categories.find_one({"_id":ObjectId(category_id)})
    if not category:
        flash("Category Not Found","danger")
    else:
        # Delete Category
        db.categories.update_one({"_id":ObjectId(category_id)},{"$set":{"status":False}})
        flash("Category Deleted Successfully","success")

    return redirect(url_for("admin_categories"))


@app.route("/admin/countries/")
def admin_countries():
    country = ""
    country_id = request.args.get("country_id")
    # Edit Categories
    if country_id:
        country = db.countries.find_one({"_id":ObjectId(country_id)})

    countries = db.countries.find({"status":True})
    countries = list(countries)
    list.reverse(countries)
    
    return render_template("/admin/countries.html",country=country, countries=countries)

@app.route("/admin/countries/", methods=['POST'])
def admin_post_country():
    country_name = request.form.get("country_name")
    country_id = request.form.get("country_id")
    if not country_id:
        # Add Country
        db.countries.insert_one({"country_name":country_name, "status":True})
        flash("Country Added Successfully","success")
    else:
        # Update Country
        db.countries.update_one({"_id":ObjectId(country_id)},{"$set":{"country_name":country_name}})
        flash("Country Updates Successfully","success")

    return redirect(url_for("admin_countries"))


# delete countries
@app.route("/admin/country/delete/<country_id>/", methods=['GET'])
def admin_delete_country(country_id):
    country = db.countries.find_one({"_id":ObjectId(country_id)})
    if not country:
        flash("Country Not Found","danger")
    else:
        # Delete Country
        db.countries.update_one({"_id":ObjectId(country_id)},{"$set":{"status":False}})
        flash("country Deleted Successfully","success")

    return redirect(url_for("admin_countries"))


# admin - view registered hosts 
@app.route("/admin/hosts/")
def admin_hosts():
    hosts = db.hosts.find()
    hosts = list(hosts)
    list.reverse(hosts)
    return render_template("/admin/hosts.html", hosts=hosts)

@app.route("/admin/verify-host/<host_id>/", methods=['GET','POST'])
def admin_verify_host(host_id):
    host = db.hosts.find_one({"_id":ObjectId(host_id)})
    if not host:
        return abort(404, "Host Not Found")
    
    if request.method == "POST":
        values = {
            "is_verified":True,
            "commission_percentage":float(request.form.get("commission_percentage"))
        }
        result = db.hosts.update_one({"_id":ObjectId(host['_id'])},{"$set":values})
        if result.modified_count > 0:
            flash("Host Verified Successfully", "success")
            return redirect(url_for("admin_hosts"))
        
    return render_template("/admin/host_update_commission.html", host=host)

@app.route("/admin/host-update-commission/<host_id>/", methods=['GET','POST'])
def admin_host_update_commission(host_id):
    host = db.hosts.find_one({"_id":ObjectId(host_id)})
    if not host:
        return abort(404, "Host Not Found")
    
    if request.method == "POST":
        values = {
            "commission_percentage":float(request.form.get("commission_percentage"))
        }
        result = db.hosts.update_one({"_id":ObjectId(host['_id'])},{"$set":values})
        if result.modified_count > 0:
            flash("Host Commisssion Updated Successfully", "success")
            return redirect(url_for("admin_hosts"))
        else:
            flash("No changes in commission value", "success")
            return redirect(url_for("admin_hosts"))
        
    return render_template("/admin/host_update_commission.html", host=host)


@app.route("/admin/properties/<host_id>/")
def admin_view_host_properties(host_id):
    properties = db.properties.aggregate([
        {"$match":{"host_id":ObjectId(host_id), "status":True}},
        {
            "$lookup": {
                "from": db.categories.name,
                "localField": "category_id",
                "foreignField": "_id",                
                "as": "category"
            }
        },
        {
            "$lookup": {
                "from": db.countries.name,
                "localField": "country_id",
                "foreignField": "_id",                
                "as": "country"
            }
        }
    ])
    properties = list(properties)
    list.reverse(properties)
    return render_template("/admin/properties.html", properties=properties)

@app.route("/admin/view-property/<property_id>/")
def admin_view_property(property_id):
    property = db.properties.aggregate([
        {"$match":{"_id":ObjectId(property_id)}},
        {
            "$lookup": {
                "from": db.categories.name,
                "localField": "category_id",
                "foreignField": "_id",                
                "as": "category"
            }
        },
        {
            "$lookup": {
                "from": db.countries.name,
                "localField": "country_id",
                "foreignField": "_id",                
                "as": "country"
            }
        }
    ])
    if not property:
        return abort(404, "Property Not Found")
    property = list(property)

    reviews = db.ratings.aggregate([
        {"$match":{"property_id":ObjectId(property[0]["_id"])}},
        {
            "$lookup": {
                "from": db.users.name,
                "localField": "user_id",
                "foreignField": "_id",                
                "as": "user"
            }
        }
    ])
    reviews = list(reviews)
    list.reverse(reviews)
    return render_template("/admin/property-details.html", property=property[0], reviews=reviews)

@app.route("/admin/bookings/<property_id>/")
def admin_view_host_bookings(property_id):
    bookings = db.bookings.aggregate([
        {"$match":{"property_id":ObjectId(property_id)}},
        {
            "$lookup": {
                "from": db.properties.name,
                "localField": "property_id",
                "foreignField": "_id",                
                "as": "property"
            }
        }
    ])
    bookings = list(bookings)
    list.reverse(bookings)
    return render_template("/admin/bookings.html", bookings=bookings)


@app.route("/admin/booking-details/<booking_id>/")
def admin_host_booking_details(booking_id):
    bookings = db.bookings.aggregate([
        {"$match": {"_id": ObjectId(booking_id)}},
        {
            "$lookup": {
                "from": db.properties.name,
                "localField": "property_id",
                "foreignField": "_id",
                "pipeline": [
                    {
                        "$lookup": {
                            "from": db.countries.name,
                            "localField": "country_id",
                            "foreignField": "_id",
                            "as": "country"
                        }
                    }
                ],
                "as": "property"
            }            
        },
        {
            "$lookup": {
                "from": db.payments.name,
                "localField": "_id",
                "foreignField": "booking_id",
                "as": "payment"
            }            
        }
    ])
    bookings = list(bookings)
    return render_template("/admin/booking-details.html", bookings=bookings[0])

# view transaction history
@app.route("/admin/transactions/")
def admin_commission():
    payments = db.payments.find({})
    payments = list(payments)
    list.reverse(payments)
    return render_template("/admin/transactions.html", payments=payments)



# host views
@app.route("/host-registration/", methods=['GET','POST'])
def host_registration():
    if request.method == "POST":
        values = {
            "name":request.form.get("name"),
            "email":request.form.get("email"),
            "phone":request.form.get("phone"),
            "password":request.form.get("password"),
            "is_verified":False,
            "status":True
        }

        db.hosts.insert_one(values)
        flash("host registered successfully, admin will verify your registration shortly","success")
        return redirect(url_for("host_login"))
        
    return render_template("host_registration.html")

@app.route("/host/")
@app.route("/host/login/", methods=['GET','POST'])
def host_login():
    error_msg = ""
    if request.method == "POST":
        values = {
            "email":request.form.get("email"),
            "password":request.form.get("password")
        }
        host = db.hosts.find_one(values)
        if host:
            if host["is_verified"]:
                session['logged_in'] = True
                session['host_id'] = str(host["_id"])
                session['fullname'] = host["name"]
                session["role"] = "Host"
                if 'about' in host:
                    return redirect(url_for("host_home"))
                else:
                    return redirect(url_for("host_profile"))
            else:
                error_msg = "Pending for verification"
        else:
            error_msg = "Invalid Login Credentials"

    return render_template("/host/login.html", error_msg=error_msg)

@app.route("/host/home/")
def host_home():
    properties = db.properties.find({"host_id":ObjectId(session["host_id"]),"status":True})
    print(session["host_id"])
    # property_count = db.properties.count_documents({"host_id":ObjectId(session["host_id"])})
    property_count = db.properties.count_documents({"host_id": ObjectId(session["host_id"]), "status": True})
    bookings = 0
    for property in properties:
        booking = db.bookings.count_documents({"property_id":ObjectId(property["_id"])})
        bookings = bookings + booking
    
    users = db.users.count_documents({"status":True})
    dashboard = {
        "properties":property_count,
        "users":users,
        "bookings":bookings
    }
    return render_template("/host/home.html", dashboard=dashboard)

@app.route("/host/my-profile/", methods=['GET', 'POST'])
def host_profile():
    if request.method == "POST":
        host_id = ObjectId(session['host_id'])
        update_values = {
            "name":request.form.get("name"),
            "phone":request.form.get("phone"),
            "languages":request.form.get("languages"),
            "about":request.form.get("about")
        }
        result = db.hosts.update_one({"_id":host_id},{"$set":update_values})
        if result.modified_count > 0:
            flash("Profile Updated Successfully", "success")
            return redirect(url_for("host_profile"))

    profile = db.hosts.find_one({"_id":ObjectId(session['host_id'])})
    return render_template("/host/profile.html", profile=profile)

# host change password
@app.route("/host/change-password/", methods=['GET','POST'])
def host_change_password():
    if request.method == "POST":
        values = {
            "password":request.form.get("password"),
        }
        result = db.hosts.update_one({"_id":ObjectId(session["host_id"])},{"$set":values})
        flash("Password Updated successfully","success")
        return redirect(url_for("host_change_password"))
    
    return render_template("/host/change-password.html")

@app.route("/host/properties/")
def host_properties():
    host_id = session["host_id"]
    host = db.hosts.find_one({"_id":ObjectId(host_id)})
    properties = db.properties.aggregate([
        {"$match":{"host_id":ObjectId(host_id), "status":True}},
        {
            "$lookup": {
                "from": db.categories.name,
                "localField": "category_id",
                "foreignField": "_id",                
                "as": "category"
            }
        },
        {
            "$lookup": {
                "from": db.countries.name,
                "localField": "country_id",
                "foreignField": "_id",                
                "as": "country"
            }
        }
    ])
    return render_template("/host/properties.html", properties=properties, host=host)

@app.route("/host/add-property/", methods=['GET','POST'])
def host_add_property():

    if request.method == "POST":
        host_id = session['host_id']
        property_image = request.files.get('property_image')
        values = {
            "host_id":ObjectId(host_id),
            "category_id":ObjectId(request.form.get("category_id")),
            "country_id":ObjectId(request.form.get("country_id")),
            "city":request.form.get("city"),
            "property_name":request.form.get("property_name"),
            "rate_per_night":float(request.form.get("rate_per_night")),
            "service_charge":float(request.form.get("service_charge")),
            "cancellation_charge":float(request.form.get("cancellation_charge")),
            "max_guest":int(request.form.get("max_guest")),
            "property_description":request.form.get("property_description"),
            "property_address":request.form.get("property_address"),
            "amenities":request.form.get("amenities"),
            "image_filename":property_image.filename,
            "status":True
        }
        db.properties.insert_one(values)
        property_image.save(APP_ROOT+"/property/"+property_image.filename)
        flash("Property Added Successfully", "success")
        return redirect(url_for("host_properties"))

    property = ""
    categories = db.categories.find({"status":True})
    countries = db.countries.find({"status":True})

    return render_template("/host/property_save.html", property=property, categories=categories, countries=countries)

@app.route("/host/edit-property/<property_id>/", methods=['GET','POST'])
def host_edit_property(property_id):
    host_id = session['host_id']

    if request.method == "POST":

        image_filename = request.form.get('image_filename')
        property_image = request.files.get('property_image')
        property_id = request.form.get('property_id')

        if property_image.filename != "":
            image_filename = property_image.filename

        values = {
            "category_id":ObjectId(request.form.get("category_id")),
            "country_id":ObjectId(request.form.get("country_id")),
            "city":request.form.get("city"),
            "property_name":request.form.get("property_name"),
            "rate_per_night":float(request.form.get("rate_per_night")),
            "service_charge":float(request.form.get("service_charge")),
            "cancellation_charge":float(request.form.get("cancellation_charge")),
            "max_guest":int(request.form.get("max_guest")),
            "property_description": request.form.get("property_description"),
            "property_address":request.form.get("property_address"),
            "amenities":request.form.get("amenities"),
            "image_filename":image_filename,
            "status":True
        }
        db.properties.update_one({"_id":ObjectId(property_id)},{"$set":values})
        # Save property image if uploaded
        if property_image.filename != "":
            property_image.save(APP_ROOT+"/property/"+property_image.filename)
            #os.remove(APP_ROOT+"/property/"+request.form.get('image_filename'))

        flash("Property Updated Successfully", "success")
        return redirect(url_for("host_properties"))

    property = db.properties.find_one({"_id":ObjectId(property_id),"host_id":ObjectId(host_id)})
    if not property:
        return abort(404, "Property Not Found")
    categories = db.categories.find({"status":True})
    countries = db.countries.find({"status":True})

    return render_template("/host/property_save.html", property=property, categories=categories, countries=countries)

@app.route("/host/view-property/<property_id>/")
def host_view_property(property_id):
    property = db.properties.aggregate([
        {"$match":{"_id":ObjectId(property_id)}},
        {
            "$lookup": {
                "from": db.categories.name,
                "localField": "category_id",
                "foreignField": "_id",                
                "as": "category"
            }
        },
        {
            "$lookup": {
                "from": db.countries.name,
                "localField": "country_id",
                "foreignField": "_id",                
                "as": "country"
            }
        }
    ])
    if not property:
        return abort(404, "Property Not Found")
    property = list(property)

    reviews = db.ratings.aggregate([
        {"$match":{"property_id":ObjectId(property[0]["_id"])}},
        {
            "$lookup": {
                "from": db.users.name,
                "localField": "user_id",
                "foreignField": "_id",                
                "as": "user"
            }
        }
    ])
    reviews = list(reviews)
    list.reverse(reviews)
    return render_template("/host/property_details.html", property=property[0], reviews=reviews)


@app.route("/host/delete-property/<property_id>/")
def host_delete_property(property_id):
    property = db.properties.find_one({"_id":ObjectId(property_id)})
    if not property:
        return abort(404, "Property Not Found")
    
    # Delete Property
    db.properties.update_one({"_id":ObjectId(property_id)},{"$set":{"status":False}})
    flash("Property Deleted Successfully","success")
    return redirect(url_for("host_properties"))


@app.route("/host/bookings/<property_id>/")
def host_bookings(property_id):
    bookings = db.bookings.aggregate([
        {"$match":{"property_id":ObjectId(property_id)}},
        {
            "$lookup": {
                "from": db.properties.name,
                "localField": "property_id",
                "foreignField": "_id",                
                "as": "property"
            }
        }
    ])
    bookings = list(bookings)
    list.reverse(bookings)
    return render_template("/host/bookings.html", bookings=bookings)

@app.route("/host/booking-details/<booking_id>/")
def host_booking_details(booking_id):
    bookings = db.bookings.aggregate([
        {"$match": {"_id": ObjectId(booking_id)}},        
        {
            "$lookup": {
                "from": db.users.name,
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }            
        },
        {
            "$lookup": {
                "from": db.properties.name,
                "localField": "property_id",
                "foreignField": "_id",
                "pipeline": [
                    {
                        "$lookup": {
                            "from": db.countries.name,
                            "localField": "country_id",
                            "foreignField": "_id",
                            "as": "country"
                        }
                    }
                ],
                "as": "property"
            }            
        },
        {
            "$lookup": {
                "from": db.payments.name,
                "localField": "_id",
                "foreignField": "booking_id",
                "as": "payment"
            }            
        }
    ])
    bookings = list(bookings)

    return render_template("/host/booking-details.html", bookings=bookings[0])

@app.route("/host/check-in/<booking_id>/")
def host_checkin(booking_id):
    bookings = db.bookings.find_one({"_id":ObjectId(booking_id)})
    db.bookings.update_one({"_id":ObjectId(bookings["_id"])},{"$set":{"is_checked_in":True}})
    flash("User checked-in successfully", "success")
    return redirect(url_for("host_bookings", property_id=bookings["property_id"]))


@app.route("/host/check-out/<booking_id>/")
def host_checkout(booking_id):
    bookings = db.bookings.find_one({"_id":ObjectId(booking_id)})
    db.bookings.update_one({"_id":ObjectId(bookings["_id"])},{"$set":{"is_checked_out":True}})
    flash("User checked-out successfully", "success")
    return redirect(url_for("host_bookings", property_id=bookings["property_id"]))


@app.route("/host/payment-history/")
def host_payment_history():
    payments = db.payments.find({"host_id":ObjectId(session["host_id"])})
    payments = list(payments)
    list.reverse(payments)
    return render_template("/host/payment-history.html", payments=payments)




# default views
@app.route("/user-registration/", methods=['GET','POST'])
def user_registration():
    if request.method == "POST":
        values = {
            "fullname":request.form.get("fullname"),
            "email":request.form.get("email"),
            "contact_no":request.form.get("contact_no"),
            "password":request.form.get("password"),
            "status":True
        }
        result = db.users.insert_one(values)
        user = db.users.find_one({"_id":ObjectId(result.inserted_id)})
        if result.inserted_id:
            session['logged_in'] = True
            session['user_id'] = str(user["_id"])
            session['fullname'] = user["fullname"]
            session["role"] = "User"
            flash("Registered successfully","success")
            return redirect(url_for("index"))
    return render_template("/register.html")

@app.route("/user-login/", methods=["GET", "POST"])
def user_login():
    error_msg = ""
    if request.method == "POST":
        values = {
            "email":request.form.get("email"),
            "password":request.form.get("password")
        }
        user = db.users.find_one(values)
        if user:
            session['logged_in'] = True
            session['user_id'] = str(user["_id"])
            session['fullname'] = user["fullname"]
            session["role"] = "User"
            
            return redirect(url_for("index"))
        else:
            error_msg = "Invalid Login Credentials"

    return render_template("/login.html", error_msg=error_msg)

@app.route("/my-profile/", methods=['GET','POST'])
def user_profile():
    if request.method == "POST":
        values = {
            "fullname":request.form.get("fullname"),
            "contact_no":request.form.get("contact_no"),
        }
        result = db.users.update_one({"_id":ObjectId(session['user_id'])},{"$set":values})
        flash("Profile Updated successfully","success")
        return redirect(url_for("user_profile"))
    
    user = db.users.find_one({"_id":ObjectId(session['user_id'])})
    return render_template("/profile.html", user=user)

@app.route("/change-password/", methods=['GET','POST'])
def user_change_password():
    if request.method == "POST":
        values = {
            "password":request.form.get("password"),
        }
        result = db.users.update_one({"_id":ObjectId(session['user_id'])},{"$set":values})
        flash("Password Updated successfully","success")
        return redirect(url_for("user_change_password"))
    
    return render_template("/change-password.html")

@app.route("/")
@app.route("/home/")
def index():
    categories = list(db.categories.find({"status":True}))
    countries = list(db.countries.find({"status":True}))
    latest_properties = db.properties.find({"status":True}).sort("_id",-1).limit(6)
    return render_template("index.html", countries=countries, categories=categories, latest_properties=latest_properties, getCountry = db.getCountryById, ratings=db.getRatingsByPropertyId)


@app.route("/property-details/<property_id>/")
def property_details(property_id):
    property = db.properties.aggregate([
        {"$match":{"_id":ObjectId(property_id)}},
        {
            "$lookup": {
                "from": db.categories.name,
                "localField": "category_id",
                "foreignField": "_id",                
                "as": "category"
            }
        },
        {
            "$lookup": {
                "from": db.countries.name,
                "localField": "country_id",
                "foreignField": "_id",                
                "as": "country"
            }
        },
        {
            "$lookup": {
                "from": db.hosts.name,
                "localField": "host_id",
                "foreignField": "_id",                
                "as": "host"
            }
        }
    ])
    if not property:
        return abort(404, "Property Not Found")
    property = list(property)
    tomorrow = datetime.now() + timedelta(1)
    tomorrow = tomorrow.strftime('%Y-%m-%d')
    ratings = db.getRatingsByPropertyId(property[0]["_id"])
    #reviews = db.ratings.find({"property_id":ObjectId(property[0]["_id"])})

    reviews = db.ratings.aggregate([
        {"$match":{"property_id":ObjectId(property[0]["_id"])}},
        {
            "$lookup": {
                "from": db.users.name,
                "localField": "user_id",
                "foreignField": "_id",                
                "as": "user"
            }
        }
    ])
    reviews = list(reviews)
    list.reverse(reviews)
    return render_template("/property_details.html", property=property[0], tomorrow=tomorrow, ratings=ratings, reviews=reviews)


# search or filter properties based on conditions
@app.route("/search/")
def search_properties():
    category_id = request.args.get("category")
    country_id = request.args.get("country")   

    if country_id ==""  and  category_id =="":
        query = {}
    if country_id !=""  and  category_id == "":
        query = {"country_id": ObjectId(country_id)}
    if country_id == ""  and category_id !="" :
        query = {"category_id": ObjectId(category_id)}
    if country_id !=""  and category_id !="":
        query = {"country_id": ObjectId(country_id),"category_id": ObjectId(category_id)}
    query["status"] = True
   
    properties = db.properties.find(query)
    properties = list(properties)

    categories = list(db.categories.find({"status":True}))
    countries = list(db.countries.find({"status":True}))

    return render_template("/search_properties.html", str=str, categories=categories, countries=countries, properties=properties, getCountry = db.getCountryById, ratings=db.getRatingsByPropertyId)

def isPropertyReserved(check_in, check_out, propertyId):
    check_in = datetime.strptime(check_in, '%Y-%m-%d')
    check_out = datetime.strptime(check_out, '%Y-%m-%d')
    query = {"property_id": ObjectId(propertyId), "is_cancelled": False}
    print(type(check_in))
    print(query)
    Bookings = db.bookings.find(query)
    for Booking in Bookings:
        print("inside")
        booked_check_in = Booking['check_in']
        booked_check_out = Booking['check_out']
        if check_in >= booked_check_in and check_in <= booked_check_out:
            return True
        elif check_out >= booked_check_in and check_out <= booked_check_out:
            return True
        elif check_in < booked_check_in and check_out > booked_check_out:
            return True
        print(check_in >= booked_check_in)
    return False

@app.route("/check-availability/", methods=['POST'])
def user_check_property_availability():

    prop_id = request.form.get("property_id")
    check_in = request.form.get("check_in")
    check_out = request.form.get("check_out")
    
    if isPropertyReserved(check_in, check_out, prop_id):
        return render_template("/confirm-booking.html", isReserved=True, booking_values = "")
    else:  
        property = db.properties.find_one({"_id":ObjectId(prop_id)})
        rate_per_night = float(property["rate_per_night"])
        total_nights = int(request.form.get("nights_count"))
        property_amount = rate_per_night * total_nights
        service_amount = round(property_amount * (float(property["service_charge"]) / 100), 2)
        total_amount = property_amount + service_amount

        booking_values = {
        "property" : property,
        "guest_count" : request.form.get("guests"),
        "check_in" : check_in,
        "check_out" : check_out,
        "total_nights" :  total_nights,
        "property_amount":property_amount,
        "service_amount":service_amount,
        "total_amount":total_amount
        }
        return render_template("/confirm-booking.html",isReserved=False, booking_values = booking_values)


@app.route("/book/", methods=['POST'])
def user_property_booking():
    property_id = request.form.get("property_id")
    property = db.properties.find_one({"_id":ObjectId(property_id)})
    
    values = {
        "user_id": ObjectId(session["user_id"]),        
        "property_id": ObjectId(property_id),
        "booked_on": datetime.now(),
        "check_in": datetime.strptime(request.form.get("check_in"), '%Y-%m-%d'),
        "check_out": datetime.strptime(request.form.get("check_out"), '%Y-%m-%d'),
        "total_guest" : int(request.form.get("total_guest")),
        "rate_per_night" : float(request.form.get("rate_per_night")),
        "total_nights" : int(request.form.get("total_nights")),       
        "bill_amount" : round(float(request.form.get("total_amount")),2),         
        "is_checked_in":False,
        "is_checked_out":False,
        "is_cancelled":False
    }
    result = db.bookings.insert_one(values)
    booking_id = result.inserted_id

    bookings = db.bookings.find_one({"_id":ObjectId(booking_id)})
    host = db.hosts.find_one({"_id":ObjectId(property["host_id"])})
    commission_amount = float(bookings["bill_amount"]) * (float(host["commission_percentage"]) / 100)
    host_amount = float(bookings["bill_amount"]) - commission_amount    

    card_values = {
        "card_holder":request.form.get("card_holder"),
        "card_number":request.form.get("card_number"),
        "expiry_month":int(request.form.get("expiry_month")),
        "expiry_year":int(request.form.get("expiry_year")),
        "cvv":int(request.form.get("cvv")),
    }
    payment_values = {
        "booking_id":ObjectId(booking_id),
        "host_id":ObjectId(host["_id"]),
        "payment_date":datetime.now(),
        "base_amount" : round(float(request.form.get("property_amount")),2),
        "service_charge" : round(float(request.form.get("service_charge")),2),
        "service_amount" : round(float(request.form.get("service_amount")),2),
        "bill_amount":round(float(bookings["bill_amount"]),2),
        "commission_percentage":round(float(host["commission_percentage"]),2),
        "commission_amount":round(float(commission_amount),2),
        "host_amount" : round(host_amount,2),
        "card_details":card_values,
        "is_cancelled":False,
        "remarks":"Property Booking"
    }
    
    result = db.payments.insert_one(payment_values)
    return redirect(url_for("user_bookings"))



@app.route("/bookings/")
def user_bookings():
    bookings = db.bookings.aggregate([
        {"$match":{"user_id":ObjectId(session["user_id"])}},
        {
            "$lookup": {
                "from": db.properties.name,
                "localField": "property_id",
                "foreignField": "_id",                
                "as": "property"
            }
        }
    ])
    bookings = list(bookings)
    list.reverse(bookings)
    return render_template("/bookings.html", bookings=bookings)

@app.route("/booking-details/<booking_id>/")
def user_booking_details(booking_id):
    bookings = db.bookings.aggregate([
        {"$match": {"_id": ObjectId(booking_id)}},
        {
            "$lookup": {
                "from": db.properties.name,
                "localField": "property_id",
                "foreignField": "_id",
                "pipeline": [
                    {
                        "$lookup": {
                            "from": db.countries.name,
                            "localField": "country_id",
                            "foreignField": "_id",
                            "as": "country"
                        }
                    }
                ],
                "as": "property"
            }            
        },
        {
            "$lookup": {
                "from": db.payments.name,
                "localField": "_id",
                "foreignField": "booking_id",
                "as": "payment"
            }            
        }
    ])
    bookings = list(bookings)
    property_id = bookings[0]["property"][0]['_id']
    
    rating = db.ratings.find_one({"user_id":ObjectId(session['user_id']), "property_id":ObjectId(property_id)})
    return render_template("/booking-details.html", bookings=bookings[0], rating=rating)

@app.route("/cancel-booking/<bid>/")
def user_cancel_booking(bid):
    bookings = db.bookings.find_one({"_id":ObjectId(bid)})
    property = db.properties.find_one({"_id":ObjectId(bookings["property_id"])})
    
    result = db.bookings.update_one({"_id":ObjectId(bookings["_id"])}, {"$set":{"is_cancelled":True}})

    if result.modified_count > 0:
        cancellation_charge = round(float(property["cancellation_charge"]), 2)
        cancellation_amount = round(float(bookings["bill_amount"]) * (cancellation_charge/100), 2)
        refund_amount = round(float(bookings["bill_amount"]) - cancellation_amount, 2)
        values = {
            "commission_percentage":0,
            "commission_amount":0,
            "cancellation_charge":cancellation_charge,
            "cancellation_amount":cancellation_amount,
            "refund_amount":refund_amount,
            "host_amount":cancellation_amount,
            "is_cancelled":True,
            "remarks":"Booking Cancelled"
        }
        db.payments.update_one({"booking_id":ObjectId(bookings['_id'])}, {"$set":values})
        flash("Booking cancelled successfully", "success")
    else:
        flash("Unable to cancel your booking now", "danger")
    return redirect(url_for("user_bookings"))

@app.route("/check-out/<booking_id>/")
def user_checkout(booking_id):
    bookings = db.bookings.find_one({"_id":ObjectId(booking_id)})
    db.bookings.update_one({"_id":ObjectId(bookings["_id"])},{"$set":{"is_checked_out":True}})
    flash("User checked-out successfully", "success")
    return redirect(url_for("user_bookings"))


@app.route("/extend-booking/<booking_id>/", methods=["GET", "POST"])
def user_extend_booking(booking_id):
    booking = db.bookings.find_one({"_id":ObjectId(booking_id)})
    if request.method == "POST":
        next_day_to_old_check_out = request.form.get("next_day_to_old_check_out")
        new_check_out = request.form.get("new_check_out")
        old_check_out = request.form.get("old_check_out")
        #exten_check_out = datetime.strptime(request.form.get("ex_date"), '%Y-%m-%d')
        if isPropertyReserved(next_day_to_old_check_out, new_check_out, booking["property_id"]):
            return render_template("/confirm-extend-booking.html", isReserved=True, booking_values = "")
        else:
            property = db.properties.find_one({"_id":ObjectId(booking["property_id"])})
            start_date = datetime.strptime(request.form.get("old_check_out"), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get("new_check_out"), '%Y-%m-%d')
            total_nights = end_date - start_date            
            total_nights = total_nights.days           
            rate_per_night = float(property["rate_per_night"])
            base_amount = rate_per_night * total_nights
            service_amount = round(base_amount * (float(property["service_charge"]) / 100), 2)
            total_amount = base_amount + service_amount

            booking_values = {
                "booking":booking,
                "property":property,
                "old_check_out":old_check_out,
                "new_check_out":new_check_out,
                "total_nights" : total_nights,
                "base_amount":base_amount,
                "service_amount":service_amount,
                "total_amount":total_amount
            }
            return render_template("/confirm-extend-booking.html", isReserved=False, booking_values = booking_values)

    
    actual_checkout_date = booking["check_out"].strftime("%Y-%m-%d")
    extend_start_date = booking["check_out"] + timedelta(1)
    extend_start_date = extend_start_date.strftime("%Y-%m-%d")
    return render_template("/extend-booking.html", actual_checkout_date=actual_checkout_date, extend_start_date=extend_start_date, booking_id=booking["_id"])

@app.route("/extended-book/", methods=['POST'])
def user_property_exten_booking():
    booking_id = request.form.get("booking_id")
    booking = db.bookings.find_one({"_id":ObjectId(booking_id)})

    
    total_nights = int(booking["total_nights"]) + int(request.form.get("extended_nights"))
    bill_amount = float(booking["bill_amount"]) + float(request.form.get("total_amount"))

    values = {
        "extended_on": datetime.now(),
        "check_out": datetime.strptime(request.form.get("new_check_out"), '%Y-%m-%d'),
        "rate_per_night" : float(request.form.get("rate_per_night")),
        "total_nights" : total_nights,       
        "bill_amount" : round(bill_amount,2)
    }

    result = db.bookings.update_one({"_id":ObjectId(booking["_id"])},{"$set":values})    

    payment = db.payments.find_one({"booking_id":ObjectId(booking_id)})

    base_amount = float(payment["base_amount"]) + float(request.form.get("base_amount"))
    service_amount = float(payment["service_amount"]) + float(request.form.get("service_amount"))
    commission_amount = float(bill_amount) * (float(payment["commission_percentage"]) / 100)
    host_amount = float(bill_amount) - commission_amount    

    payment_values = {
        "base_amount" : round(base_amount,2),
        "service_amount" : round(service_amount,2),
        "bill_amount":round(bill_amount,2),
        "commission_amount":round(commission_amount,2),
        "host_amount" : round(host_amount,2),
        "remarks":"Booking Extended"
    }
    
    result = db.payments.update_one({"_id":ObjectId(payment["_id"])},{"$set":payment_values})
    flash("Booking extension confirmed", "success")
    return redirect(url_for("user_bookings"))

@app.route("/rating/", methods=["POST"])
def user_post_rating():
    property_id = request.form.get("property_id")
    booking_id = request.form.get("booking_id")
    values = {
        "property_id":ObjectId(property_id),
        "user_id":ObjectId(session["user_id"]),
        "rating":int(request.form.get("rating")),
        "review":request.form.get("review")
    }
    db.ratings.insert_one(values)
    flash("Ratings posted successfully", "success")
    return redirect(url_for("user_booking_details", booking_id=booking_id))


@app.route("/is-user-email-exist")
def check_user_email_registerd():
    email = request.args.get("email")
    user = db.users.find_one({"email": email})
    if user:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/is-host-email-exist")
def check_host_email_registerd():
    email = request.args.get("email")
    host = db.hosts.find_one({"email": email})
    if host:
        return jsonify(False)
    else:
        return jsonify(True)
    

@app.route("/is-user-phone-exist")
def check_user_phone_registerd():
    contact_no = request.args.get("contact_no")
    user = db.users.find_one({"contact_no": contact_no})
    if user:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/is-host-phone-exist")
def check_host_phone_registerd():
    phone = request.args.get("phone")
    host = db.hosts.find_one({"phone": phone})
    if host:
        return jsonify(False)
    else:
        return jsonify(True)



@app.route("/logout/")
def logout():
    session.clear()
    return redirect(url_for("index"))




if __name__ == '__main__':
    app.run(debug=True)