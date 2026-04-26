import os
from jinja2 import Template

# Alle Variablen aus deinem :root – Name, Label, Typ, Default
THEME_VARS = [
    # Primary Colors
    {"name": "primary-color", "label": "Primary Color", "type": "color", "default": "#2563eb"},
    {"name": "primary-dark", "label": "Primary Dark", "type": "color", "default": "#1d4ed8"},
    {"name": "primary-light", "label": "Primary Light", "type": "color", "default": "#3b82f6"},

    # Secondary Colors
    {"name": "secondary-color", "label": "Secondary Color", "type": "color", "default": "#64748b"},
    {"name": "secondary-light", "label": "Secondary Light", "type": "color", "default": "#94a3b8"},

    # Status Colors
    {"name": "success-color", "label": "Success Color", "type": "color", "default": "#10b981"},
    {"name": "warning-color", "label": "Warning Color", "type": "color", "default": "#f59e0b"},
    {"name": "danger-color", "label": "Danger Color", "type": "color", "default": "#ef4444"},
    {"name": "info-color", "label": "Info Color", "type": "color", "default": "#0ea5e9"},

    # Neutral Colors
    {"name": "dark", "label": "Dark", "type": "color", "default": "#1f2937"},
    {"name": "gray-900", "label": "Gray 900", "type": "color", "default": "#111827"},
    {"name": "gray-800", "label": "Gray 800", "type": "color", "default": "#1f2937"},
    {"name": "gray-700", "label": "Gray 700", "type": "color", "default": "#374151"},
    {"name": "gray-600", "label": "Gray 600", "type": "color", "default": "#4b5563"},
    {"name": "gray-500", "label": "Gray 500", "type": "color", "default": "#6b7280"},
    {"name": "gray-400", "label": "Gray 400", "type": "color", "default": "#9ca3af"},
    {"name": "gray-300", "label": "Gray 300", "type": "color", "default": "#d1d5db"},
    {"name": "gray-200", "label": "Gray 200", "type": "color", "default": "#e5e7eb"},
    {"name": "gray-100", "label": "Gray 100", "type": "color", "default": "#f3f4f6"},
    {"name": "gray-50", "label": "Gray 50", "type": "color", "default": "#f9fafb"},
    {"name": "white", "label": "White", "type": "color", "default": "#ffffff"},

    # Spacing
    {"name": "spacing-xs", "label": "Spacing XS", "type": "text", "default": "0.25rem"},
    {"name": "spacing-sm", "label": "Spacing SM", "type": "text", "default": "0.5rem"},
    {"name": "spacing-md", "label": "Spacing MD", "type": "text", "default": "1rem"},
    {"name": "spacing-lg", "label": "Spacing LG", "type": "text", "default": "1.5rem"},
    {"name": "spacing-xl", "label": "Spacing XL", "type": "text", "default": "2rem"},
    {"name": "spacing-2xl", "label": "Spacing 2XL", "type": "text", "default": "3rem"},

    # Shadows
    {"name": "shadow-sm", "label": "Shadow SM", "type": "text", "default": "0 1px 2px 0 rgba(0, 0, 0, 0.05)"},
    {"name": "shadow", "label": "Shadow", "type": "text", "default": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"},
    {"name": "shadow-md", "label": "Shadow MD", "type": "text", "default": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"},
    {"name": "shadow-lg", "label": "Shadow LG", "type": "text", "default": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"},
    {"name": "shadow-xl", "label": "Shadow XL", "type": "text", "default": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"},

    # Radius
    {"name": "radius-sm", "label": "Radius SM", "type": "text", "default": "0.375rem"},
    {"name": "radius-md", "label": "Radius MD", "type": "text", "default": "0.5rem"},
    {"name": "radius-lg", "label": "Radius LG", "type": "text", "default": "0.75rem"},
    {"name": "radius-full", "label": "Radius Full", "type": "text", "default": "9999px"},

    # Transitions
    {"name": "transition-fast", "label": "Transition Fast", "type": "text", "default": "150ms ease-in-out"},
    {"name": "transition", "label": "Transition", "type": "text", "default": "250ms ease-in-out"},
    {"name": "transition-slow", "label": "Transition Slow", "type": "text", "default": "350ms ease-in-out"},

    # Typography
    {"name": "font-family", "label": "Font Family", "type": "text", "default": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'},
    {"name": "font-mono", "label": "Font Mono", "type": "text", "default": '"Courier New", monospace'},
    {"name": "line-height-tight", "label": "Line Height Tight", "type": "text", "default": "1.25"},
    {"name": "line-height-normal", "label": "Line Height Normal", "type": "text", "default": "1.5"},
    {"name": "line-height-relaxed", "label": "Line Height Relaxed", "type": "text", "default": "1.75"},
]

# Restliches CSS (dein Theme) ohne :root – 1:1 übernommen
BASE_CSS = r"""
/* ========================================
   Base Styles
   ======================================== */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    font-family: var(--font-family);
    font-size: 1rem;
    line-height: var(--line-height-normal);
    color: var(--gray-900);
    background-color: var(--gray-50);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ========================================
   Typography
   ======================================== */

h1, h2, h3, h4, h5, h6 {
    font-weight: 700;
    line-height: var(--line-height-tight);
    margin-bottom: var(--spacing-md);
    color: var(--gray-900);
}

h1 {
    font-size: 2.25rem;
    margin-bottom: var(--spacing-lg);
}

h2 {
    font-size: 1.875rem;
}

h3 {
    font-size: 1.5rem;
}

h4 {
    font-size: 1.25rem;
}

h5 {
    font-size: 1.125rem;
}

h6 {
    font-size: 1rem;
}

p {
    margin-bottom: var(--spacing-md);
}

a {
    color: var(--primary-color);
    text-decoration: none;
    transition: color var(--transition-fast);
}

a:hover {
    color: var(--primary-dark);
    text-decoration: underline;
}

small, .small {
    font-size: 0.875rem;
}

/* ========================================
   Container
   ======================================== */

.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--spacing-lg);
}

.container-sm {
    max-width: 640px;
}

.container-md {
    max-width: 896px;
}

.container-lg {
    max-width: 1024px;
}

.container-xl {
    max-width: 1280px;
}

/* ========================================
   Forms
   ======================================== */

.form-group {
    margin-bottom: var(--spacing-lg);
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-lg);
}

@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;
    }
}

label {
    display: block;
    margin-bottom: var(--spacing-sm);
    font-weight: 600;
    color: var(--gray-900);
    font-size: 0.95rem;
}

label.required::after {
    content: " *";
    color: var(--danger-color);
}

.form-input,
.form-textarea,
.form-select {
    width: 100%;
    padding: var(--spacing-md);
    border: 1px solid var(--gray-300);
    border-radius: var(--radius-md);
    font-family: var(--font-family);
    font-size: 1rem;
    background-color: var(--white);
    color: var(--gray-900);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.form-input:hover,
.form-textarea:hover,
.form-select:hover {
    border-color: var(--gray-400);
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-textarea {
    min-height: 150px;
    resize: vertical;
    font-family: var(--font-family);
}

.form-hint {
    display: block;
    margin-top: var(--spacing-sm);
    color: var(--gray-500);
    font-size: 0.875rem;
}

.form-error {
    color: var(--danger-color);
    font-size: 0.875rem;
    margin-top: var(--spacing-sm);
}

.form-success {
    color: var(--success-color);
    font-size: 0.875rem;
    margin-top: var(--spacing-sm);
}

.post-form {
    display: flex;
    flex-direction: column;
}

/* ========================================
   Buttons
   ======================================== */

.btn {
    display: inline-block;
    padding: var(--spacing-md) var(--spacing-lg);
    border: none;
    border-radius: var(--radius-md);
    font-family: var(--font-family);
    font-size: 1rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
    text-align: center;
    user-select: none;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Primary Button */
.btn-primary {
    background-color: var(--primary-color);
    color: var(--white);
    box-shadow: var(--shadow-sm);
}

.container {
    animation: pageOpen 0.6s ease-out forwards;
    transform-origin: center center;
    opacity: 0;
    transform: scale(0.85);
}

@keyframes pageOpen {
    0% {
        opacity: 0;
        transform: scale(0.85);
    }
    60% {
        opacity: 1;
        transform: scale(1.02);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}

.btn-primary:hover:not(:disabled) {
    background-color: var(--primary-dark);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
    color: white;
}
.title-main-index {
    font-size: 3rem;
    font-weight: 700;
    color: white;
    margin-bottom: var(--spacing-md);
}
.subtitle {
    color: white;
}
.btn-primary:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}

/* Secondary Button */
.btn-secondary {
    background-color: var(--gray-200);
    color: var(--gray-900);
    box-shadow: var(--shadow-sm);
}

.btn-secondary:hover:not(:disabled) {
    background-color: var(--gray-300);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

.btn-secondary:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}

/* Success Button */
.btn-success {
    background-color: var(--success-color);
    color: var(--white);
    box-shadow: var(--shadow-sm);
}

.btn-success:hover:not(:disabled) {
    background-color: #059669;
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

/* Danger Button */
.btn-danger {
    background-color: var(--danger-color);
    color: var(--white);
    box-shadow: var(--shadow-sm);
}

.btn-danger:hover:not(:disabled) {
    background-color: #dc2626;
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

/* Button Sizes */
.btn-sm {
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: 0.875rem;
}

.btn-lg {
    padding: var(--spacing-lg) var(--spacing-xl);
    font-size: 1.125rem;
}

/* Button Groups */
.form-actions {
    display: flex;
    gap: var(--spacing-md);
    margin-top: var(--spacing-xl);
}

/* ========================================
   Cards
   ======================================== */

.card {
    background-color: var(--white);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
    transition: box-shadow var(--transition-fast), transform var(--transition-fast);
    overflow: hidden;
}

.card:hover {
    box-shadow: var(--shadow-md);
}

.card-header {
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--gray-200);
    background-color: var(--gray-50);
}

.card-body {
    padding: var(--spacing-lg);
}

.card-footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--gray-200);
    background-color: var(--gray-50);
}

/* ========================================
   Admin Layout
   ======================================== */

.admin-header {
    margin-bottom: var(--spacing-2xl);
    padding-bottom: var(--spacing-xl);
    border-bottom: 2px solid var(--primary-color);
}

.admin-header h1 {
    margin-bottom: var(--spacing-sm);
    color: var(--gray-900);
}

.subtitle {
    color: var(--gray-600);
    font-size: 1.125rem;
    margin: 0;
}

/* ========================================
   Tables
   ======================================== */

.table {
    width: 100%;
    border-collapse: collapse;
    background-color: var(--white);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow);
}

.table thead {
    background-color: var(--gray-50);
    border-bottom: 1px solid var(--gray-200);
}

.table th {
    padding: var(--spacing-md) var(--spacing-lg);
    text-align: left;
    font-weight: 600;
    color: var(--gray-900);
    border-bottom: 2px solid var(--gray-300);
}

.table td {
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--gray-200);
}

.table tbody tr:hover {
    background-color: var(--gray-50);
}

.table tbody tr:last-child td {
    border-bottom: none;
}

/* ========================================
   Alerts
   ======================================== */

.alert {
    padding: var(--spacing-lg);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-lg);
    border-left: 4px solid;
}

.alert-success {
    background-color: #ecfdf5;
    border-color: var(--success-color);
    color: #065f46;
}

.alert-error,
.alert-danger {
    background-color: #fef2f2;
    border-color: var(--danger-color);
    color: #7f1d1d;
}

.alert-warning {
    background-color: #fffbeb;
    border-color: var(--warning-color);
    color: #78350f;
}

.alert-info {
    background-color: #f0f9ff;
    border-color: var(--info-color);
    color: #082f49;
}

/* ========================================
   Navigation
   ======================================== */

.navbar {
    background-color: var(--white);
    box-shadow: var(--shadow);
    padding: var(--spacing-lg) var(--spacing-xl);
    margin-bottom: var(--spacing-2xl);
}

.navbar-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
    text-decoration: none;
}

.navbar-nav {
    display: flex;
    gap: var(--spacing-lg);
    list-style: none;
}

.navbar-nav a {
    color: var(--gray-700);
    text-decoration: none;
    font-weight: 500;
    transition: color var(--transition-fast);
}

.navbar-nav a:hover {
    color: var(--primary-color);
}

/* ========================================
   Utility Classes
   ======================================== */

.text-center {
    text-align: center;
}

.text-left {
    text-align: left;
}

.text-right {
    text-align: right;
}

.text-muted {
    color: var(--gray-500);
}

.text-primary {
    color: var(--primary-color);
}

.text-success {
    color: var(--success-color);
}

.text-danger {
    color: var(--danger-color);
}

.mt {
    margin-top: var(--spacing-md);
}

.mb {
    margin-bottom: var(--spacing-md);
}

.p {
    padding: var(--spacing-md);
}

.hidden {
    display: none;
}

.flex {
    display: flex;
}

.flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.gap-md {
    gap: var(--spacing-md);
}

.gap-lg {
    gap: var(--spacing-lg);
}

/* ========================================
   Responsive Design
   ======================================== */

@media (max-width: 768px) {
    h1 {
        font-size: 1.875rem;
    }

    h2 {
        font-size: 1.5rem;
    }

    .container {
        padding: var(--spacing-md);
    }

    .form-row {
        grid-template-columns: 1fr;
    }

    .form-actions {
        flex-direction: column;
    }

    .btn {
        width: 100%;
    }
}

/* ========================================
   TinyMCE Customization
   ======================================== */

.tox .tox-editor-container {
    border: 1px solid var(--gray-300) !important;
    border-radius: var(--radius-md) !important;
}

.tox .tox-editor-header {
    background-color: var(--gray-50) !important;
}

.tox .tox-tbtn:hover {
    background-color: var(--gray-200) !important;
}

.tox .tox-tbtn--active {
    background-color: var(--primary-color) !important;
    color: var(--white) !important;
}

.tox-fullscreen {
    z-index: 1000 !important;
}

/* ========================================
   Print Styles
   ======================================== */

@media print {
    body {
        background-color: var(--white);
    }

    .btn,
    .navbar {
        display: none;
    }

    .container {
        max-width: 100%;
        padding: 0;
    }
}
"""

ROOT_TEMPLATE = Template(""":root {
{% for var, value in vars.items() %}
    --{{ var }}: {{ value }};
{% endfor %}
}

""")

def generate_theme_file(form_data: dict, output_path: str):
    # Map Form → CSS-Variablen
    # Note: form keys use dashes (e.g., "primary-color") not underscores
    vars_dict = {}
    for v in THEME_VARS:
        key = v["name"]
        # Try both dash and underscore versions for compatibility
        value = form_data.get(key) or form_data.get(key.replace("-", "_")) or v["default"]
        # Strings mit Anführungszeichen korrekt behandeln
        if '"' in value or "'" in value:
            vars_dict[key] = value
        else:
            vars_dict[key] = value

    root_block = ROOT_TEMPLATE.render(vars=vars_dict)
    css = "/* Generated Theme */\n" + root_block + BASE_CSS

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(css)
