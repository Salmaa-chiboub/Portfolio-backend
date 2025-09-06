# Email Templates

This directory contains HTML email templates for the authentication system.

## Available Templates

### 1. Password Reset Email (`password_reset_email.html`)
- **Purpose**: Sent to users when they request a password reset
- **Variables**:
  - `reset_link`: The URL to reset the password
  - `user`: The user object (contains first_name, last_name, email)

## Adding New Templates

1. Create a new HTML file in this directory
2. Use Django template syntax for dynamic content
3. Include inline CSS (most email clients don't support external stylesheets)
4. Test with various email clients before deploying

## Testing Emails in Development

In development, emails are printed to the console by default. You can configure a real email backend in your `.env` file if needed.

## Styling Guidelines

- Use tables for layout (better email client compatibility)
- Keep styles inline
- Use web-safe fonts (Arial, Helvetica, sans-serif)
- Test with dark mode in mind
- Ensure good contrast for accessibility
- Keep email width under 600px

## Email Service Configuration

Update your `.env` file with the appropriate email settings. See the root `.env.example` for configuration examples for different providers (Gmail, Mailgun, SendGrid).
