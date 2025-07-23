from nicegui import app, ui
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from urllib.parse import quote_plus, unquote_plus
import stripe
from stripe.error import SignatureVerificationError
import os
import sys
import boto3
import hmac
import hashlib
import base64
import logging
from dotenv import load_dotenv
import jwt
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define unrestricted routes that don't require authentication
unrestricted_page_routes = {'/', '/login', '/signup', '/forgot-password', '/health', '/confirm-signup'}

# Authentication will be handled directly in the page functions instead of middleware
# This avoids conflicts with NiceGUI's response handling

VERSION = "250722-1725"

# Log environment variables
logger.info(f"Starting NiceGUI application...{VERSION}")
logger.info(f"PORT environment variable: {os.getenv('PORT', '8000')}")
logger.info(f"ENVIRONMENT environment variable: {os.getenv('ENVIRONMENT', 'not set')}")

# AWS Cognito settings (ideally from env)
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-west-2_123456789012")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "<YOUR_COGNITO_CLIENT_ID>") # TODO: Replace with actual Cognito client ID
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET", "<YOUR_COGNITO_CLIENT_SECRET>") # TODO: Replace with actual Cognito client secret
COGNITO_REGION = os.getenv("AWS_REGION", "us-west-2")

logger.info(f"COGNITO_USER_POOL_ID: {COGNITO_USER_POOL_ID}")
logger.info(f"COGNITO_CLIENT_ID: {COGNITO_CLIENT_ID}")
logger.info(f"COGNITO_CLIENT_SECRET: {COGNITO_CLIENT_SECRET}")  
logger.info(f"COGNITO_REGION: {COGNITO_REGION}")

# Create Cognito client
cognito = boto3.client('cognito-idp', region_name=COGNITO_REGION)

# Stripe Price IDs for subscription plans
STRIPE_PRICE_ID_TRIAL = os.getenv("STRIPE_PRICE_ID_TRIAL", "MISSING_STRIPE_PRICE_ID_TRIAL")
STRIPE_PRICE_ID_BASIC = os.getenv("STRIPE_PRICE_ID_BASIC", "MISSING_STRIPE_PRICE_ID_BASIC") 
STRIPE_PRICE_ID_PREMIUM = os.getenv("STRIPE_PRICE_ID_PREMIUM", "MISSING_STRIPE_PRICE_ID_PREMIUM")

# Stripe API configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "MISSING_STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "MISSING_STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "MISSING_STRIPE_WEBHOOK_SECRET")


# Logic for submitting reset link to Cognito
def send_reset_link(email):
    if not email:
        ui.notify('Email is required')
        return

    try:
        secret_hash = calculate_secret_hash(email)
        cognito.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            SecretHash=secret_hash
        )
        logger.info(f'Password reset code sent to {email}')
        ui.notify(f'Password reset code sent to {email}')
        ui.navigate.to('/login')
    except cognito.exceptions.UserNotFoundException:
        logger.warning(f'User not found: {email}')
        ui.notify('User not found')
    except Exception as e:
        logger.error(f'Error: {str(e)}')
        ui.notify(f'Error: {str(e)}')

def handle_login_button():
    logger.info("handle_login_button")
    ui.navigate.to('/login')

def handle_signup_button():
    logger.info("handle_signup_button")
    ui.navigate.to('/signup')

def authenticate_user(email, password, redirect_to: str = '/dashboard'):
    """
    Authenticate user with Cognito and store in app.storage.user
    """
    logger.info(f"authenticate_user: {email}")  # Removed password from log
    if not email or not password:
        ui.notify('Email and Password are required')
        return
    
    try:
        # Calculate the SECRET_HASH
        secret_hash = calculate_secret_hash(email)

        # Attempt to authenticate with Cognito
        response = cognito.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )

        # If authentication is successful, extract the JWT token (ID token)
        id_token = response['AuthenticationResult']['IdToken']
        logger.info(f"User {email} successfully authenticated")

        # Store authentication state in app.storage.user (server-side session)
        app.storage.user.update({
            'authenticated': True,
            'id_token': id_token,
            'email': email
        })
        
        logger.info(f"Stored authentication in app.storage.user for {email}")

        # Navigate to the intended destination or dashboard
        logger.info(f"Navigating to {redirect_to}")
        ui.navigate.to(redirect_to)
        
    except cognito.exceptions.UserNotFoundException:
        logger.error(f"User {email} not found")
        ui.notify(f"User {email} not found")
    except cognito.exceptions.UserNotConfirmedException:
        logger.error(f"User {email} not confirmed")
        ui.notify(f"User {email} not confirmed. Please check your email for a confirmation code.")
        ui.navigate.to(f'/confirm-signup?email={email}')
    except cognito.exceptions.NotAuthorizedException:
        logger.error("Incorrect username or password.")
        ui.notify("Incorrect username or password.")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        ui.notify(f"Error: {str(e)}")


def handle_remember_me(event=None):
    logger.info(f"handle_remember_me: {event}")
    # TODO: Implement remember me, which needs to put a cookie in the browser
    pass

def calculate_secret_hash(email):
    """
    Calculate the SECRET_HASH for the sign-up request.
    """
    message = email + COGNITO_CLIENT_ID
    secret_hash = hmac.new(
        bytes(COGNITO_CLIENT_SECRET, 'utf-8'),
        bytes(message, 'utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(secret_hash).decode()

def handle_signup_submit(email, password, confirm_password):
    logger.info(f"handle_signup_submit: {email}, {password}, {confirm_password}")

    if not email or not password or not confirm_password:
        ui.notify('Email, Password, and Confirm Password are required')
        return
    
    if password != confirm_password:
        ui.notify('Passwords do not match')
        return  
    
    try:
        secret_hash = calculate_secret_hash(email)

        cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                }
            ],
            SecretHash=secret_hash
        )
        logger.info(f"User {email} successfully signed up part 1")
        ui.notify(f"Look for confirmation code in your email: {email}")
        encoded_email = quote_plus(email)
        logger.info(f"Redirecting to /confirm-signup for {email}, {encoded_email}")
        ui.navigate.to(f'/confirm-signup/{encoded_email}')
    except cognito.exceptions.UsernameExistsException:
        logger.error(f"User {email} already exists")
        ui.notify(f"User {email} already exists")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        ui.notify(f"Error: {str(e)}")

def send_confirmation_code(email, code):
    logger.info(f"send_confirmation_code: {email}, {code}")
    try:
        secret_hash = calculate_secret_hash(email)

        cognito.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=code,
            SecretHash=secret_hash
        )
        logger.info(f"User {email} successfully confirmed")
        ui.notify(f"User {email} successfully confirmed")
        ui.navigate.to('/login')
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        ui.notify(f"Error: {str(e)}")


def handle_cancel():
    ui.navigate.to('/')

def handle_plan_trial():
    # Make this free for one week
    logger.info("handle_plan_trial")
    pass

def handle_plan_basic():
    # Make this $10/month
    logger.info("handle_plan_basic")
    pass

def handle_plan_premium(): 
    # Make this $95/month
    logger.info("handle_plan_premium")
    pass

# Home Page
@ui.page('/')
def home():
    """Home page with split layout and two auth buttons"""
    ui.add_head_html('<style>body { margin: 0; padding: 0; }</style>')
    with ui.column().classes('w-full h-screen'):
        with ui.row().classes('w-full h-full'):
            # Left side - Content Section
            with ui.column().style('flex: 1').classes('h-full p-8 flex flex-col justify-center'):
                ui.label('Stripe Test Page').classes('text-4xl font-bold mb-4')
                ui.label('Cognito Login flow, followed by Stripe test subscriptions').classes('text-lg mb-8')
                with ui.column().classes('space-y-2'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('check_circle').classes('text-green-500 text-xl')
                        ui.label('Verify AWS deployment to AppRunner').classes('text-sm')
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('person_add').classes('text-blue-500 text-xl')
                        ui.label('Test AWS Cognito sign-up flow').classes('text-sm')
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('webhook').classes('text-purple-500 text-xl')
                        ui.label(f'Test Stripe subscription webhooks - {VERSION}').classes('text-sm')
            # Right side - Auth Buttons
            with ui.column().style('flex: 1').classes('h-full flex items-center justify-center p-8'):
                with ui.card().classes('w-96 rounded-xl shadow-lg p-6'):
                    with ui.row().classes('w-full gap-4'):
                        ui.button('Login', on_click=lambda: ui.navigate.to('/login')).classes('flex-1 py-2 px-4 bg-blue-600 text-white rounded-l-lg border-2 border-blue-600')
                        ui.button('Sign Up', on_click=lambda: ui.navigate.to('/signup')).classes('flex-1 py-2 px-4 bg-blue-600 text-white text-blue-600 rounded-r-lg border-2 border-blue-600')


# Login Page - Modified to handle redirect_to parameter
@ui.page('/login')
def login(redirect_to: str = '/dashboard'):
    """Login page with centered form and redirect support"""
    logger.info(f"Login page, redirect_to: {redirect_to}")
    # If already authenticated, redirect to intended destination
    if app.storage.user.get('authenticated', False):
        ui.navigate.to(redirect_to)
        return
    
    ui.add_head_html('<style>body { margin: 0; padding: 0; }</style>')
    with ui.column().classes('w-full h-screen justify-center items-center'):
        with ui.card().classes('w-96 p-8'):
            ui.label('Login').classes('text-2xl font-bold text-center mb-6')
            email = ui.input(label='Email').classes('w-full mb-4')
            password = ui.input(label='Password', password=True).classes('w-full mb-4')
            with ui.row().classes('w-full justify-between items-center mb-6'):
                ui.checkbox('Remember me', on_change=handle_remember_me).classes('text-sm')
                ui.link('Forgot Password?', '#').classes('text-blue-600 hover:text-blue-800 text-sm cursor-pointer').on('click', lambda: ui.navigate.to('/forgot-password'))
            with ui.row().classes('w-full justify-between'):
                ui.button('Cancel', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 hover:bg-gray-600')
                ui.button('Login', on_click=lambda: authenticate_user(email.value, password.value, redirect_to)).classes('bg-blue-600 hover:bg-blue-700')

# Sign-up Page
@ui.page('/signup')
def signup():
    """Sign-up page with centered form"""
    logger.info("Sign-up page")
    ui.add_head_html('<style>body { margin: 0; padding: 0; }</style>')
    with ui.column().classes('w-full h-screen justify-center items-center'):
        with ui.card().classes('w-96 p-8'):
            ui.label('Sign Up').classes('text-2xl font-bold text-center mb-6')
            email = ui.input(label='Email').classes('w-full mb-4')
            password = ui.input(label='Password', password=True).classes('w-full mb-4')
            confirm_password = ui.input(label='Confirm Password', password=True).classes('w-full mb-6')
            with ui.row().classes('w-full justify-between'):
                ui.button('Cancel', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 hover:bg-gray-600')
                ui.button('Create Account', on_click=lambda: handle_signup_submit(email.value, password.value, confirm_password.value   )).classes('bg-blue-600 hover:bg-blue-700')

# Confirmation Code Page
@ui.page('/confirm-signup/{encoded_email}')
def confirm_signup(encoded_email):
    """Confirmation code page with centered form"""
    ui.add_head_html('<style>body { margin: 0; padding: 0; }</style>')

    # Get the email from the URL query parameters using NiceGUI's client
    email_value = unquote_plus(encoded_email)
    logger.info(f"Confirmation code page for {email_value}, {encoded_email}")

    with ui.column().classes('w-full h-screen justify-center items-center'):
        with ui.card().classes('w-96 p-8'):
            ui.label('Confirmation Code').classes('text-2xl font-bold text-center mb-6')
            ui.label(f'Confirmation code sent to {email_value}').classes('w-full mb-4')
            code = ui.input(label='Code').classes('w-full mb-4')
            with ui.row().classes('w-full justify-between'):
                ui.button('Cancel', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 hover:bg-gray-600')
                ui.button('Submit', on_click=lambda: send_confirmation_code(email_value, code.value)).classes('bg-blue-600 hover:bg-blue-700')

""" alternative way to do this
from jose import jwt, JWTError  # pip install python-jose

@ui.page('/dashboard')
def dashboard(request):
    "" "Dashboard page with plan selection" ""  # remove space between ""

    token = request.cookies.get('id_token')
    if not token:
        ui.notify("Access denied: not logged in.")
        ui.navigate.to('/login')
        return

    try:
        # Validate token (use your actual Cognito config here)
        decoded = jwt.decode(token, JWKS_PUBLIC_KEY, algorithms=['RS256'], audience=COGNITO_CLIENT_ID)
        logger.info(f"Authenticated user: {decoded['email']}")
    except JWTError:
        ui.notify("Invalid token")
        ui.navigate.to('/login')
        return
"""
# Dashboard Page - Simplified authentication check
@ui.page('/dashboard')
def dashboard():
    """Dashboard page with plan selection"""
    logger.info("Dashboard page")
    # Authentication is now handled by middleware, so we can access user info directly
    email = app.storage.user.get('email', 'User')
    
    ui.add_head_html('<style>body { margin: 0; padding: 0; }</style>')
    with ui.column().classes('w-full h-screen justify-center items-center'):
        ui.label(f'Welcome, {email}!').classes('text-2xl font-bold text-center mb-4')
        ui.label('Choose Your Plan').classes('text-3xl font-bold text-center mb-8')
        with ui.row().classes('gap-6'):
            ui.button('Trial', on_click=handle_plan_trial).classes('bg-green-600 hover:bg-green-700 text-white px-8 py-4 text-lg')
            ui.button('Basic', on_click=handle_plan_basic).classes('bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg')
            ui.button('Premium', on_click=handle_plan_premium).classes('bg-purple-600 hover:bg-purple-700 text-white px-8 py-4 text-lg')
        
        # Add logout button
        ui.button('Logout', on_click=lambda: logout()).classes('mt-8 bg-red-600 hover:bg-red-700 text-white px-6 py-2')

def logout():
    """Logout function to clear authentication state"""
    app.storage.user.clear()
    ui.navigate.to('/')

# Forgot Password Page
@ui.page('/forgot-password')
def forgot_password():
    """Forgot password page with centered form"""
    logger.info("Forgot password page")
    ui.add_head_html('<style>body { margin: 0; padding: 0; }</style>')
    with ui.column().classes('w-full h-screen justify-center items-center'):
        with ui.card().classes('w-96 p-8'):
            ui.label('Forgot Password').classes('text-2xl font-bold text-center mb-6')
            email = ui.input(label='Email').classes('w-full mb-4')
            with ui.row().classes('w-full justify-between'):
                ui.button('Cancel', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 hover:bg-gray-600')
                ui.button('Send Reset Link', on_click=lambda: send_reset_link(email.value)).classes('bg-blue-600 hover:bg-blue-700')


# Health Check Page (leave untouched)
# @ui.page('/health')
# def health_check():
#     """Health check endpoint for AppRunner"""
#     return JSONResponse(
#         content={
#             'status': 'healthy',
#             'service': 'nicegui-stripe-test',
#             'environment': os.getenv('ENVIRONMENT', 'not set'), 
#             'version': VERSION
#         },
#         status_code=200
#     )

@app.get("/health")
def health_check():
    """Health check endpoint for AppRunner"""
    return JSONResponse(
        content={
            'status': 'healthy',
            'service': 'nicegui-stripe-test',
            'environment': os.getenv('ENVIRONMENT', 'not set'), 
            'version': VERSION
        },
        status_code=200
    )

# Stripe Webhook Endpoint
@app.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for subscription management"""
    logger.info("Stripe webhook endpoint called")
    
    # TODO: Implement webhook handling logic
    # - Verify webhook signature
    # - Parse event data
    # - Handle subscription events (created, updated, cancelled, etc.)
    # - Update user subscription status in database/storage
    
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    
    logger.debug(f"Stripe webhook received. sig: {sig}")
    logger.debug(f"Stripe webhook received. payload: {payload}")

    if not sig:
        raise HTTPException(status_code=401, detail="No signature provided")
    
    try:
        webhook_secret = get_stripe_parameter("STRIPE_WEBHOOK_SECRET")
        event = stripe.Webhook.construct_event(
            payload, sig, webhook_secret
        )
    except SignatureVerificationError as e:
        logger.warning(f"Verify this is correct webhook_secret: _{mask_secret_key(webhook_secret)}_")
        logger.error(f"HTTP 401: Invalid signature: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid signature: {str(e)}")
    except Exception as e:
        logger.error(f"HTTP 400: Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    data = event["data"]["object"]


    return JSONResponse(
        content={"status": "webhook received"},
        status_code=200
    )

def get_stripe_parameter(param_name):
    """Get Stripe parameter from environment variables"""
    return os.getenv(param_name, "")

def mask_secret_key(key, visible_chars=4):
    """Mask a secret key for logging"""
    if not key or len(key) <= visible_chars:
        return "*" * len(key) if key else ""
    return "*" * (len(key) - visible_chars) + key[-visible_chars:]

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access to authenticated pages.
    
    Redirects unauthenticated users to the login page for protected routes.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check if user is authenticated using app.storage.user
        logger.info(f"AuthMiddleware: {request.url.path}")
        if not app.storage.user.get('authenticated', False):
            # Allow access to unrestricted routes and NiceGUI internal routes
            if (not request.url.path.startswith('/_nicegui') and 
                not any(request.url.path.startswith(route) for route in unrestricted_page_routes)):
                # Redirect to login with the intended destination
                logger.info(f"Redirecting to login for {request.url.path}")
                return RedirectResponse(f'/login?redirect_to={request.url.path}')
            
        logger.info(f"AuthMiddleware: {request.url.path} allowed")
        return await call_next(request)

# Add the middleware to the app
# Add CORS middleware first (before AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.awsapprunner.com",
        "https://*.amazonaws.com",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add the authentication middleware
app.add_middleware(AuthMiddleware)

if __name__ in {"__main__", "__mp_main__"}:
    try:
        Path("logs").mkdir(exist_ok=True)
        logger.info("Creating logs directory...")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Application will bind to: 0.0.0.0:{os.getenv('PORT', '8000')}")
        logger.info("Starting NiceGUI server...")
        ui.run(
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            reload=False,
            show=False,
            title="Stripe Test Environment",
            storage_secret='StripeTestEnvironmentSecretAbc123'
        )
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)