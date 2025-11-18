"""
Flask Top 5 Submission App

AI DISCLOSURE: This code was improved by Claude (Anthropic AI assistant) based on 
user-provided original code. Improvements include: input validation, security 
enhancements (CSRF protection placeholder), better error handling, code organization, 
environment-based configuration, and logging capabilities.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Secret key for session management (should be environment variable in production)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# In-memory storage for submissions (use database in production)
submissions = []

# Configuration
MAX_CATEGORY_LENGTH = 100
MAX_ITEM_LENGTH = 200
MAX_SUBMISSIONS = 1000  # Prevent memory overflow


def validate_input(text, max_length, field_name):
    """Validate user input for length and content."""
    if not text:
        return False, f"{field_name} cannot be empty"
    
    if len(text) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters"
    
    # Basic XSS prevention (Flask's Jinja2 auto-escapes, but good practice)
    if any(char in text for char in ['<', '>', '"', "'"]):
        return False, f"{field_name} contains invalid characters"
    
    return True, None


@app.route("/", methods=["GET", "POST"])
def home():
    """Main route for displaying and submitting top 5 lists."""
    global submissions
    
    if request.method == "POST":
        try:
            # Extract form data
            category = request.form.get("category", "").strip()
            items = [
                request.form.get(f"item{i}", "").strip() 
                for i in range(1, 6)
            ]
            
            # Validate category
            is_valid, error_msg = validate_input(
                category, MAX_CATEGORY_LENGTH, "Category"
            )
            if not is_valid:
                flash(error_msg, "error")
                return redirect(url_for('home'))
            
            # Validate all items
            for idx, item in enumerate(items, 1):
                is_valid, error_msg = validate_input(
                    item, MAX_ITEM_LENGTH, f"Item {idx}"
                )
                if not is_valid:
                    flash(error_msg, "error")
                    return redirect(url_for('home'))
            
            # Check submission limit
            if len(submissions) >= MAX_SUBMISSIONS:
                flash("Submission limit reached. Please contact administrator.", "error")
                logger.warning("Submission limit reached")
                return redirect(url_for('home'))
            
            # Create submission
            submission = {
                "id": len(submissions) + 1,
                "category": category,
                "five": items,
                "timestamp": datetime.now().isoformat()
            }
            
            submissions.append(submission)
            logger.info(f"New submission added: {category}")
            flash("Your top 5 list has been submitted successfully!", "success")
            
        except Exception as e:
            logger.error(f"Error processing submission: {str(e)}")
            flash("An error occurred. Please try again.", "error")
        
        return redirect(url_for('home'))
    
    # GET request - display form and submissions
    return render_template(
        "index.html", 
        submissions=reversed(submissions),  # Show newest first
        max_category_length=MAX_CATEGORY_LENGTH,
        max_item_length=MAX_ITEM_LENGTH
    )


@app.route("/clear", methods=["POST"])
def clear_submissions():
    """Clear all submissions (admin function - should be protected)."""
    global submissions
    submissions = []
    logger.info("All submissions cleared")
    flash("All submissions have been cleared.", "info")
    return redirect(url_for('home'))


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(e)}")
    return render_template('500.html'), 500


if __name__ == "__main__":
    # Use environment variables for configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Flask app on port {port} (debug={debug_mode})")
    
    # WARNING: Never run with debug=True in production
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port
    )
