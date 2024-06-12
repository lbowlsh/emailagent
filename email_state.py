# email_state.py

class EmailState:
    def __init__(self):
        self.emails = []
        self.categorized_emails = {}
        self.sales_info = []
        self.inquiry_info = []
        self.product_strategy = None
        self.draft_email = None

    def add_email(self, email):
        self.emails.append(email)

    def categorize_email(self, email_id, category):
        email = next((e for e in self.emails if e['id'] == email_id), None)
        if email:
            if category not in self.categorized_emails:
                self.categorized_emails[category] = []
            self.categorized_emails[category].append(email)

    def add_sales_info(self, info):
        self.sales_info.append(info)

    def set_product_strategy(self, strategy):
        self.product_strategy = strategy

    def save_draft_email(self, draft):
        self.draft_email = draft

    def get_email_by_id(self, email_id):
        return next((e for e in self.emails if e['id'] == email_id), None)
