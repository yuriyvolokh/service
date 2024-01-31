import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify  # added to top of file
from flask_restful import Api
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
db = SQLAlchemy(app)


class Product(db.Model):
    __tablename__ = "Products"

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, unique=True, index=True)
    price = db.Column(db.Integer, unique=True, index=True)


class Category(db.Model):
    __tablename__ = "Category"

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, unique=True, index=True)


class TreeCategory(db.Model):
    __tablename__ = "TreeCategory"
    ancestor = db.Column(db.Integer, primary_key=True)
    descendant = db.Column(db.Integer, primary_key=True)


@app.route('/api/products', methods=['GET'])
def products():
    products = Product.query.all()
    json_products = []
    for product in products:
        json_products.appnd({"name": product.name, "price": product.price})

    return jsonify(json_products)


@app.route('/api/products/add', methods=['POST'])
def api_product_add():
    product_json = request.get_json()
    product = Product(name=product_json["name"], price=product_json["price"])
    db.session.add(product)
    db.session.commit()
    return jsonify({"status": "successful"})


@app.route('/api/products/<product_id>', methods=['GET'])
def api_get_product(product_id):
    product = Product.query.filter_by(id=product_id)
    return jsonify({"name": product.name, "price": product.price})


@app.route('/api/products/update', methods=['PUT'])
def api_update_products():
    product_json = request.get_json()
    product = Product.query.filter_by(id=product_json["id"]).first()
    product.name = product_json["name"]
    product.price = product_json["price"]
    db.session.commit()
    return jsonify({"status": "successful"})


@app.route('/api/products/delete/<product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    Product.query.filter_by(id=product_id).first().delete()
    db.session.commit()
    return jsonify({"status": "successful"})


@app.route('/api/categories', methods=['GET'])
def categories():
    categories = Category.query.all()
    json_categories = []
    for category in categories:
        json_categories.appnd({"name": category.name})

    return jsonify(json_categories)


@app.route('/api/categories/add', methods=['POST'])
def api_category_add():
    category_json = request.get_json()
    category = Category(name=category_json["name"])
    db.session.add(category)
    db.session.commit()


@app.route('/api/category/<category_id>', methods=['GET'])
def api_get_category(category_id):
    category = Category.query.filter_by(id=category_id)
    return jsonify({"name": category.name})


@app.route('/api/category/update', methods=['PUT'])
def api_update_category():
    category_json = request.get_json()
    category = Category.query.filter_by(id=category_json["id"]).first()
    category.name = category_json["name"]
    db.session.commit()
    return jsonify({"status": "successful"})


@app.route('/api/category/delete/<category_id>', methods=['DELETE'])
def api_delete_category(category_id):
    Category.query.filter_by(id=category_id).first().delete()
    db.session.commit()
    return jsonify({"status": "successful"})


@app.route('/api/category/parent/update', methods=['PUT'])
def api_update_parent_category():
    category_json = request.get_json()
    parent_category = TreeCategory.query.filter_by(descendant=category_json["id"]).first()
    parent_category_obj = Category.query.filter_by(id=parent_category.id).first()
    parent_category_obj.name = category_json["name"]
    db.session.commit()
    return jsonify({"status": "successful"})


@app.route('/api/products/categories', methods=['GET'])
def api_categories_from_products():
    payload = request.get_json()
    products = payload.get("products")
    set_products = set(products)
    query = db.session.query(Product.id).filter(Product.name.in_(set_products))
    results = query.all()
    set_product_ids = [item[0] for item in results]
    categories_obj = db.session.query(TreeCategory.ancestor).filter(
            TreeCategory.descendant.in_(set_product_ids)).all()
    category_ids = [item[0] for item in categories_obj]
    category_names = [Category.query.filter_by(id=category_id).first().name for category_id in category_ids]

    return jsonify(category_names)


@app.route('/api/category/products', methods=['GET'])
def api_products_from_categories():
    def products_from_categories(set_category_ids):
        products_or_category_obj = db.session.query(TreeCategory.descendant).filter(
                TreeCategory.ancestor.in_(set_category_ids)).all()
        product_or_category_ids = [item[0] for item in products_or_category_obj]
        return product_or_category_ids

    payload = request.get_json()
    categories = payload.get("categories")
    set_categories = set(categories)
    set_category_ids = [item[0] for item in db.session.query(Category.id).filter(Category.name.in_(set_categories)).all()]
    full_set_category_ids = [item[0] for item in db.session.query(Category.id).all()]

    product_or_category_ids = products_from_categories(set_category_ids)
    product_ids = []
    i = 0
    while i < len(product_or_category_ids):
        item = product_or_category_ids[i]
        if item in full_set_category_ids:
            product_ids.extend(products_from_categories([item]))
        else:
            product_ids.append(item)
        i += 1

    # finds category_id and replace it with all products ids
    product_names = [Product.query.filter_by(id=product_id).first().name for product_id in product_ids]

    return jsonify(product_names)


@app.route('/api/category/counts', methods=['GET'])
def api_products_counts_from_categories():
    result_json = {}
    payload = request.get_json()
    categories = payload.get("categories")
    set_categories = set(categories)
    results = db.session.query(Category.id).filter(Category.name.in_(set_categories)).all()
    category_ids = [item[0] for item in results]
    for category, category_id in zip(categories, category_ids):
        products_obj = db.session.query(TreeCategory.ancestor, TreeCategory.descendant).filter_by(
                ancestor=category_id).count()
        result_json[category] = products_obj

    return jsonify(result_json)


@app.route('/api/category/total_count', methods=['GET'])
def api_product_count_from_categories():
    payload = request.get_json()
    categories = payload.get("categories")
    set_categories = set(categories)
    results = db.session.query(Category.id).filter(Category.name.in_(set_categories)).all()
    set_category_ids = [item[0] for item in results]
    product_count = db.session.query(TreeCategory.descendant).filter(
            TreeCategory.ancestor.in_(set_category_ids)).count()

    return jsonify({"total": product_count})


if __name__ == "__main__":
    api = Api(app, prefix="/api/v1")
    '''swagger specific'''
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "My Rest App"
        }
    )

    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    app.run()
