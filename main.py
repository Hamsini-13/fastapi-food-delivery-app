from fastapi import FastAPI, Query, Response
from pydantic import BaseModel, Field
import math

app = FastAPI(title="QuickBite Food Delivery")

# ------------------------------
# DATA
# ------------------------------

menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 250, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Veg Burger", "price": 120, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Chicken Burger", "price": 150, "category": "Burger", "is_available": True},
    {"id": 4, "name": "Coke", "price": 50, "category": "Drink", "is_available": True},
    {"id": 5, "name": "Chocolate Cake", "price": 180, "category": "Dessert", "is_available": False},
    {"id": 6, "name": "Pepsi", "price": 50, "category": "Drink", "is_available": True}
]

orders = []
order_counter = 1

cart = []

# ------------------------------
# DAY 3 HELPER FUNCTIONS
# ------------------------------

def find_menu_item(item_id):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None


def calculate_bill(price, quantity, order_type):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total


def filter_menu_logic(category=None, max_price=None, is_available=None):

    result = []

    for item in menu:

        if category is not None and item["category"] != category:
            continue

        if max_price is not None and item["price"] > max_price:
            continue

        if is_available is not None and item["is_available"] != is_available:
            continue

        result.append(item)

    return result


# ------------------------------
# DAY 1 GET ROUTES
# ------------------------------

@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}


@app.get("/menu")
def get_menu():
    return {"total_items": len(menu), "items": menu}


@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}


@app.get("/menu/summary")
def menu_summary():

    available = [i for i in menu if i["is_available"]]
    unavailable = [i for i in menu if not i["is_available"]]

    categories = list(set([i["category"] for i in menu]))

    return {
        "total_items": len(menu),
        "available": len(available),
        "unavailable": len(unavailable),
        "categories": categories
    }


# ------------------------------
# DAY 3 FILTER
# ------------------------------

@app.get("/menu/filter")
def filter_menu(
    category: str = None,
    max_price: int = None,
    is_available: bool = None
):

    result = filter_menu_logic(category, max_price, is_available)

    return {"count": len(result), "items": result}


# ------------------------------
# DAY 6 SEARCH / SORT / PAGE
# ------------------------------

@app.get("/menu/search")
def search_menu(keyword: str):

    result = [
        i for i in menu
        if keyword.lower() in i["name"].lower()
        or keyword.lower() in i["category"].lower()
    ]

    if not result:
        return {"message": "No items found"}

    return {"total_found": len(result), "items": result}


@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):

    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by"}

    if order not in ["asc", "desc"]:
        return {"error": "Invalid order"}

    sorted_menu = sorted(menu, key=lambda x: x[sort_by])

    if order == "desc":
        sorted_menu.reverse()

    return {"sort_by": sort_by, "order": order, "items": sorted_menu}


@app.get("/menu/page")
def menu_page(page: int = 1, limit: int = 3):

    start = (page - 1) * limit
    items = menu[start:start + limit]

    total_pages = math.ceil(len(menu) / limit)

    return {
        "page": page,
        "limit": limit,
        "total": len(menu),
        "total_pages": total_pages,
        "items": items
    }


@app.get("/menu/browse")
def browse_menu(
    keyword: str = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):

    result = menu

    if keyword:
        result = [
            i for i in result
            if keyword.lower() in i["name"].lower()
            or keyword.lower() in i["category"].lower()
        ]

    result = sorted(result, key=lambda x: x[sort_by])

    if order == "desc":
        result.reverse()

    start = (page - 1) * limit
    paginated = result[start:start + limit]

    return {
        "page": page,
        "limit": limit,
        "total": len(result),
        "items": paginated
    }


# ------------------------------
# DAY 2 PYDANTIC MODELS
# ------------------------------

class OrderRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)
    delivery_address: str = Field(min_length=10)
    order_type: str = "delivery"


class NewMenuItem(BaseModel):
    name: str = Field(min_length=2)
    price: int = Field(gt=0)
    category: str = Field(min_length=2)
    is_available: bool = True


class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# ------------------------------
# DAY 2 POST ORDER
# ------------------------------

@app.post("/orders")
def create_order(order: OrderRequest):

    global order_counter

    item = find_menu_item(order.item_id)

    if item is None:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    total = calculate_bill(item["price"], order.quantity, order.order_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item": item["name"],
        "quantity": order.quantity,
        "total_price": total
    }

    orders.append(new_order)
    order_counter += 1

    return new_order


# ------------------------------
# DAY 4 CRUD
# ------------------------------

@app.post("/menu")
def add_menu_item(item: NewMenuItem, response: Response):

    for m in menu:
        if m["name"].lower() == item.name.lower():
            return {"error": "Item already exists"}

    new_id = len(menu) + 1

    new_item = {
        "id": new_id,
        **item.dict()
    }

    menu.append(new_item)

    response.status_code = 201

    return new_item


@app.put("/menu/{item_id}")
def update_menu(
    item_id: int,
    price: int = None,
    is_available: bool = None
):

    item = find_menu_item(item_id)

    if item is None:
        return {"error": "Item not found"}

    if price is not None:
        item["price"] = price

    if is_available is not None:
        item["is_available"] = is_available

    return item


@app.delete("/menu/{item_id}")
def delete_item(item_id: int):

    item = find_menu_item(item_id)

    if item is None:
        return {"error": "Item not found"}

    menu.remove(item)

    return {"message": "Item deleted", "name": item["name"]}


@app.get("/menu/{item_id}")
def get_menu_item(item_id: int):

    item = find_menu_item(item_id)

    if item is None:
        return {"error": "Item not found"}

    return item


# ------------------------------
# DAY 5 CART WORKFLOW
# ------------------------------

@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):

    item = find_menu_item(item_id)

    if item is None or not item["is_available"]:
        return {"error": "Item unavailable"}

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"message": "Quantity updated", "cart": cart}

    cart.append({
        "item_id": item_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": quantity
    })

    return {"message": "Item added", "cart": cart}


@app.get("/cart")
def view_cart():

    total = sum(i["price"] * i["quantity"] for i in cart)

    return {"cart": cart, "grand_total": total}


@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):

    for item in cart:
        if item["item_id"] == item_id:
            cart.remove(item)
            return {"message": "Item removed"}

    return {"error": "Item not in cart"}


@app.post("/cart/checkout")
def checkout(data: CheckoutRequest, response: Response):

    global order_counter

    if not cart:
        return {"error": "Cart is empty"}

    placed_orders = []
    grand_total = 0

    for item in cart:

        total = item["price"] * item["quantity"]

        new_order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item": item["name"],
            "quantity": item["quantity"],
            "total_price": total
        }

        orders.append(new_order)
        placed_orders.append(new_order)

        order_counter += 1
        grand_total += total

    cart.clear()

    response.status_code = 201

    return {"orders": placed_orders, "grand_total": grand_total}
