import os
import stripe
from flask import jsonify
import backend.models as models

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