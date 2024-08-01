import os
import stripe
from flask import jsonify, request
import backend.models as models
import logging

# Set your Stripe API key
stripe.api_key = os.environ.get("STRIPE_API_KEY")
#TODO fill this when developing locally (from developers website stripe)
local_secret = 'whsec_0f311b199e4ef699d3f394a2d3786ff39cc5350e16818877f74d9a0252a94eda'

#create an in memory cache for payment_id and status
payment_cache = {}


def process_webhook(payload, sig_header):
    event = None
    try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, local_secret
            )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        #TODO update payment status in the database or do what you need to
        payment_cache[payment_intent.id] = payment_intent.status
    
    print(payment_cache)
    
    return jsonify(success=True)

def create_payment_link(product_id, price=50, currency="mxn"):
    try:
        price = stripe.Price.create(
        currency=currency,
        price=price,
        custom_unit_amount={"enabled": True},
        product=product_id,
        )
        link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}])
        
        return link
    except stripe.error.StripeError as e:
        # Handle any errors from Stripe
        print(f"Error creating payment link: {str(e)}")
        return None

    
# function to check if payments is made from APi
def check_payment_status(payment_intent_id):
    if payment_intent_id in payment_cache:
        return payment_cache[payment_intent_id]
    else:
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if payment_intent.status == 'succeeded':
                # update cache with payment status
                payment_cache[payment_intent_id] = payment_intent.status
                return True
            return False
        except stripe.error.StripeError as e:
            print(f"Error checking payment status: {str(e)}")
            return False

#checkout session for api voice        
def create_checkout_voice_ai(voice_id):
    url = f"custom_voice/{voice_id}"
    name = "AI Voice Clone"
    description = "Create your own AI voice clone"
    checkout = create_checkout_session(url, 5000, "mxn", name, description)
    return checkout

def create_checkout_session(url, amount=5000, currency="mxn", name="Payment", description="Payment for Services"):
    print("Creating checkout session in Stripe ")
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': currency,
                        'unit_amount': amount,  # $20.00
                        'product_data': {
                            'name': name,
                            'description': description,
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.host_url + url,
            cancel_url=request.host_url + url,
        )
        return {
            'id': checkout_session.id,
            'url': checkout_session.url
        }
    except Exception as e:
        print("Error creating checkout session", e)
        return jsonify(error=str(e)), 403
    
def get_payment_status(payment_id):
    try:
        payment = stripe.checkout.Session.retrieve(payment_id)
        response = {
            'payed': payment.payment_status == "paid",
            'url': payment.url
        }
        return response
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise f"Stripe error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise f"Unexpected error: {str(e)}"
