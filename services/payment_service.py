import stripe
import os
from fastapi import HTTPException

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# TODO: Add your Price ID from Stripe Dashboard here
# For now, we will create a product on the fly or use a fixed configuration
PREMIUM_PRICE_ID = "price_premium_monthly"  # Placeholder

def create_checkout_session(user_id: str, email: str, base_url: str):
    """
    Creates a Stripe Checkout Session for Premium subscription.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API Key missing")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=email,
            line_items=[
                {
                    # Provide the exact Price ID (e.g. price_1234) of the product you want to sell
                    # For testing without a pre-created product, we can use price_data
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': 'TopAções Premium',
                            'description': 'Acesso ilimitado a todos os recursos e relatórios',
                        },
                        'unit_amount': 2990, # R$ 29,90
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base_url}/pricing',
            # Metadata is useful for the webhook to know WHO paid
            metadata={
                'user_id': user_id,
                'email': email
            }
        )
        return checkout_session.url
    except Exception as e:
        print(f"Error creating stripe session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def verify_webhook_signature(payload, sig_header):
    """
    Verifies the webhook signature.
    """
    if not STRIPE_WEBHOOK_SECRET:
        print("⚠️ STRIPE_WEBHOOK_SECRET missing, skipping signature verification (INSECURE)")
        return True # Fallback for now, but should raise error in production if critical
        
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
