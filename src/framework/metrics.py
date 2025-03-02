# metrics.py

def calculate_ctr(impressions, clicks):
    """
    Calculate Click-Through Rate
    
    CTR = Number of Clicks / Number of Impressions
    
    Args:
        impressions: Number of recommendation impressions
        clicks: Number of clicks on recommendations
        
    Returns:
        Float between 0 and 1 representing click-through rate
    """
    return clicks / impressions if impressions > 0 else 0

def calculate_application_rate(clicks, applications):
    """
    Calculate Application Rate
    
    Application Rate = Number of Applications / Number of Clicks
    
    Args:
        clicks: Number of clicks on recommendations
        applications: Number of job applications submitted
        
    Returns:
        Float between 0 and 1 representing application rate
    """
    return applications / clicks if clicks > 0 else 0

def calculate_time_spent(session_durations):
    """
    Calculate average time spent viewing job recommendations
    
    Args:
        session_durations: List of session durations in seconds
        
    Returns:
        Average session duration in seconds
    """
    return sum(session_durations) / len(session_durations) if session_durations else 0