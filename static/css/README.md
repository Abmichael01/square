# CSS Architecture

This directory contains the separated CSS files for better organization and maintainability.

## File Structure

### `base.css`
Contains common styles used across all pages:
- CSS reset and base typography
- Header and footer styles
- Form elements (inputs, buttons, labels)
- Common layout utilities
- Responsive design base styles

### `auth.css`
Styles specific to authentication pages:
- Login page styles
- Reset password page styles
- OTP and verification forms
- Demo notes and help text

### `dashboard.css`
Styles for dashboard and user management pages:
- Dashboard layout and navigation
- User profile sections
- Content sections and tabs
- Loading spinners
- Back buttons and navigation

### `payment.css`
Styles for payment-related pages:
- Payment method selection cards
- Bank payment forms
- Bitcoin payment interface
- Gift card payment forms
- Payment status displays

### `card.css`
Styles for credit card components and partials:
- Pure CSS credit card designs
- Light and dark card variants
- Card selection interfaces
- Card preview components

### `components.css`
Reusable UI components:
- Modal dialogs
- Alert messages
- Badges and status indicators
- Progress bars
- Tooltips
- Dropdowns
- Tabs

## Usage

All CSS files are automatically included in the base template (`templates/base.html`). The files are loaded in the following order:

1. `base.css` - Foundation styles
2. `auth.css` - Authentication styles
3. `dashboard.css` - Dashboard styles
4. `payment.css` - Payment styles
5. `card.css` - Card component styles
6. `components.css` - Reusable components

## Benefits

- **Better Organization**: Each file focuses on a specific area of the application
- **Easier Maintenance**: Changes to specific features are isolated to their respective files
- **Improved Performance**: Browsers can cache individual files
- **Team Collaboration**: Multiple developers can work on different CSS files without conflicts
- **Modularity**: Components can be easily reused across different pages

## Adding New Styles

When adding new styles:

1. **Base styles** (typography, colors, common elements) → `base.css`
2. **Page-specific styles** → appropriate page CSS file (`auth.css`, `dashboard.css`, `payment.css`)
3. **Reusable components** → `components.css`
4. **Card-related styles** → `card.css`

## Responsive Design

All CSS files include responsive design considerations with media queries for:
- Mobile devices (max-width: 480px)
- Tablets (max-width: 768px)
- Desktop and larger screens

## Browser Support

The CSS uses modern features with fallbacks for older browsers:
- CSS Grid with Flexbox fallbacks
- CSS Custom Properties (CSS Variables) where appropriate
- Modern selectors with progressive enhancement
