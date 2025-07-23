# Current UI Structure Description

## Application Overview
This is a NiceGUI-based web application for a Stripe test environment with a multi-page interface built using Python and NiceGUI framework. The application includes real AWS Cognito authentication integration and middleware-based route protection.

## Current UI Structure

### 1. Home Page (`/`)
- **Layout**: A responsive webpage with a split layout
- **Left-Side (Content Section)**: Text content with icons and descriptions
  - Large headline: "Stripe Test Page" (text-4xl font-bold mb-4)
  - Subheading: "Cognito Login flow, followed by Stripe test subscriptions" (text-lg mb-8)
  - Three feature bullet points with colored icons and descriptions:
    - Green check_circle icon: "Verify AWS deployment to AppRunner"
    - Blue person_add icon: "Test AWS Cognito sign-up flow" 
    - Purple webhook icon: "Test Stripe subscription webhooks"
  - Uses Tailwind spacing (space-y-2) and icons aligned with text
- **Right Side (Authentication Buttons)**: Centered card with two buttons
  - White background card with rounded corners and shadow (w-96 rounded-xl shadow-lg p-6)
  - Two buttons side-by-side: "Login" and "Sign Up"
  - Button styling: flex-1 py-2 px-4 with blue background and white text
  - **Navigation**: Login button navigates to `/login`, Sign Up button navigates to `/signup`
- **Styling**: Uses Tailwind CSS classes for responsive design

### 2. Login Page (`/login`)
- **Layout**: Full-screen centered form layout
- **Authentication Check**: Redirects authenticated users to intended destination
- **Form Container**: Card component (w-96 p-8) containing:
  - "Login" header (text-2xl font-bold text-center mb-6)
  - Form fields: Email input, Password input (with password=True)
  - Row with checkbox "Remember me" and blue link "Forgot Password?"
  - Button row with Cancel (gray) and Login (blue) buttons
- **Functionality**: Real AWS Cognito authentication with error handling
- **Navigation**: Cancel returns to home page, successful login navigates to dashboard
- **Styling**: Uses Tailwind CSS classes for responsive design

### 3. Sign-up Page (`/signup`)
- **Layout**: Full-screen centered form layout
- **Form Container**: Card component (w-96 p-8) containing:
  - "Sign Up" header (text-2xl font-bold text-center mb-6)
  - Form fields: Email, Password, Confirm Password (all with password=True for confirm)
  - Button row with Cancel (gray) and Create Account (blue) buttons
- **Functionality**: Real AWS Cognito signup with email confirmation flow
- **Navigation**: Cancel returns to home, successful signup redirects to confirmation page
- **Styling**: Uses Tailwind CSS classes for responsive design

### 4. Confirmation Code Page (`/confirm-signup/{encoded_email}`)
- **Layout**: Full-screen centered form layout
- **URL Parameter**: Encoded email address in URL path
- **Form Container**: Card component (w-96 p-8) containing:
  - "Confirmation Code" header (text-2xl font-bold text-center mb-6)
  - Display of email address where code was sent
  - Code input field
  - Button row with Cancel (gray) and Submit (blue) buttons
- **Functionality**: AWS Cognito email confirmation with code verification
- **Navigation**: Cancel returns to home, successful confirmation redirects to login

### 5. Dashboard Page (`/dashboard`)
- **Layout**: Full-screen centered layout
- **Authentication**: Protected by middleware, shows user email
- **Content**: 
  - Welcome message with user's email (text-2xl font-bold text-center mb-4)
  - "Choose Your Plan" header (text-3xl font-bold text-center mb-8)
- **Pricing Buttons**: Three horizontally arranged buttons:
  - Trial (green background, green-600/700 hover)
  - Basic (blue background, blue-600/700 hover)
  - Premium (purple background, purple-600/700 hover)
- **Button Styling**: Large buttons (px-8 py-4 text-lg) with white text
- **Logout Button**: Red button (mt-8 bg-red-600 hover:bg-red-700) below plan buttons
- **Styling**: Uses Tailwind CSS classes for responsive design

### 6. Forgot Password Page (`/forgot-password`)
- **Layout**: Full-screen centered form layout
- **Form Container**: Card component (w-96 p-8) containing:
  - "Forgot Password" header (text-2xl font-bold text-center mb-6)
  - Email input field
  - Button row with Cancel (gray) and Send Reset Link (blue) buttons
- **Functionality**: AWS Cognito password reset with email notification
- **Navigation**: Cancel returns to home, successful reset redirects to login

### 7. Health Check Endpoint (`/health`)
- **Purpose**: AppRunner health monitoring
- **Response**: JSON with status, service name, and environment
- **Access**: Unrestricted route, no authentication required

## Authentication System
- **Middleware**: AuthMiddleware class protects all routes except unrestricted ones
- **Storage**: Uses app.storage.user for server-side session data
- **Unrestricted Routes**: '/', '/login', '/signup', '/forgot-password', '/health', '/confirm-signup'
- **Redirect Logic**: Unauthenticated users redirected to login with intended destination preserved
- **Real Integration**: AWS Cognito with proper error handling for all authentication flows

## Current Functionality
- **Real Authentication**: AWS Cognito integration with proper error handling
- **Email Confirmation**: Complete signup flow with email verification
- **Password Reset**: Forgot password functionality with email notifications
- **Route Protection**: Middleware-based authentication with automatic redirects
- **Form Validation**: Client-side validation for required fields
- **Navigation**: Page-to-page navigation using ui.navigate()
- **Notifications**: User feedback using ui.notify() for errors and success messages
- **Plan Selection**: Placeholder functionality (no Stripe integration yet)

## Styling Approach
- **Framework**: Tailwind CSS classes for responsive design
- **Color Scheme**: Blue primary, gray secondary, green/purple for plans, red for logout
- **Layout**: Full-screen layouts with centered content using flexbox
- **Components**: Card-based form containers with consistent padding and shadows
- **Interactive Elements**: Hover effects on buttons and links
- **Typography**: Consistent text sizing and spacing using Tailwind classes

## Technical Stack
- **Frontend**: NiceGUI framework for UI components
- **Backend**: FastAPI for API endpoints
- **Authentication**: AWS Cognito with boto3 integration
- **Storage**: NiceGUI app.storage.user for session management
- **Logging**: Python logging configuration with stdout/stderr handlers
- **Environment**: Environment variable support with python-dotenv
- **Deployment**: Docker containerization ready for AWS AppRunner
- **Testing**: Pytest framework with NiceGUI testing fixtures support