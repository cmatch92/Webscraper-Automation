def setup_browser(browser_type, headless=True):
    """Create a standard Playwright browser, context, and page."""
    browser = browser_type.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return browser, context, page

def save_to_csv(data, filename):
    """
    Standardized data export to the data folder.
    """
    import pandas as pd
    df = pd.DataFrame(data)
    path = os.path.join('data', filename)
    df.to_csv(path, index=False)
    print(f"Data successfully saved to {path}")
