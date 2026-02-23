import re
from datetime import date, datetime

def sanitize_input(text: str) -> str:
    """
    Sanitizes input text to prevent basic XSS/Code Injection.
    Removes HTML tags and dangerous characters.
    """
    if not isinstance(text, str):
        return text
        
    # Remove HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Remove script tags
    clean = re.sub(r'javascript:', '', clean, flags=re.IGNORECASE)
    # Remove potential SQL injection chars
    clean = clean.replace("'", "''") 
    
    return clean.strip()

def validate_email(email: str) -> bool:
    """Validates an email address format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def calculate_age(born: date) -> int:
    """Calculates age from birthdate."""
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def format_currency(amount: float) -> str:
    """Formats a number as currency."""
    return "${:,.2f}".format(amount)
