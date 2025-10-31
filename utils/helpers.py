def validate_grade(value):
    """
    Validate grade input (allow float or int between 0 and 100).
    Returns (True, '', numeric_value) if valid,
            (False, 'reason', None) if invalid.
    """
    try:
        num = float(value)
    except ValueError:
        return False, 'not a number', None
    if num < 0 or num > 100:
        return False, 'must be between 0 and 100', None
    return True, '', num

def calculate_average(scores):
    """
    scores: list of numbers (floats or ints)
    """
    if not scores:
        return None
    return round(sum(scores) / len(scores), 2)

def subject_list():
    """Return list of subject keys used as columns/fields."""
    return ['math', 'science', 'english']
