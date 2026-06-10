from decimal import Decimal
from .models import Offer


def get_best_offer(product):

    product_offer = Offer.objects.filter(
        offer_type="PRODUCT", product=product, is_active=True
    ).first()

    category_offer = Offer.objects.filter(
        offer_type="CATEGORY", category=product.category, is_active=True
    ).first()

    best_offer = None

    if product_offer and category_offer:

        if product_offer.discount_value > category_offer.discount_value:

            best_offer = product_offer

        else:

            best_offer = category_offer

    elif product_offer:

        best_offer = product_offer

    elif category_offer:

        best_offer = category_offer

    return best_offer


def calculate_discounted_price(variant):

    offer = get_best_offer(variant.product)

    original_price = variant.price

    if not offer:

        return {
            "original_price": original_price,
            "final_price": original_price,
            "discount_amount": Decimal("0"),
            "offer": None,
        }

    if offer.discount_type == "PERCENTAGE":

        discount_amount = (original_price * offer.discount_value) / Decimal("100")

    else:

        discount_amount = offer.discount_value

    final_price = original_price - discount_amount

    if final_price < 0:

        final_price = Decimal("0")

    return {
        "original_price": original_price,
        "final_price": final_price,
        "discount_amount": discount_amount,
        "offer": offer,
    }
