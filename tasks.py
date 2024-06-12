from crewai import Task
from textwrap import dedent

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crewai import Task
from textwrap import dedent
from agents import EmailAgents
from pydantic import ValidationError
from salespydantic import CustomerInfo,CustomerInfoModel,SalesOpportunity,SalesOpportunityModel,SessionLocal

class EmailFilterTasks:
    def __init__(self, category_agent, emails):
        # self.agent = agent
        # self.filter_agent = filter_agent
        self.category_agent = category_agent
        self.emails = emails

    def categorize_emails_task(self):
        return Task(
            description=dedent(f"""\
                Analyze a batch of emails and filter out non-essential ones such as newsletters, promotional content and notifications.
                Categorize the filtered work-related emails into appropriate categories: sales, procurement, implementation, maintenance, or other.
                Use your expertise to accurately tag each email.
                Your final answer MUST be a list of categorized emails with their respective categories.
                EMAILS
                -------
                email tags: {self.emails}
                FORMAT:
                    - Category: {{category}}, Thread ID: {{thread_id}}, Sender: {{sender}}
                """),
                
            agent=self.category_agent,
            expected_output="Categorized emails in the specified format."
        )
    


class SalesTasks:
    def __init__(self, sales_agent, categorized_emails):
        self.sales_agent = sales_agent
        self.categorized_emails = categorized_emails

    def extract_customer_info_task(self):
        return Task(
            description=dedent(f"""\
               Extract customer information from sales-related emails.

                Use your expertise in email content analysis to identify key customer details such as name, contact information, and specific inquiries.

                 Categorized EMAILS
                -------
                {self.categorized_emails}
                Your final answer MUST be the extracted customer information in the following format:
                - email id: {{thread_id}}, sender: {{sender}}, content:{{content}}
                - Customer Name: {{customer_name}}, Contact Info: {{contact_info}}, Inquiry: {{inquiry}}
                """),
            agent=self.sales_agent,
            expected_output="Extracted customer information in the specified format."
        )
    def update_state_with_customer_info(self, result, state):
        state['sales_info'].extend(result['extracted_customer_info'])
    
    def save_customer_info(self, customer_info:dict):
        try:
            validated_info = CustomerInfo(**customer_info)
        except ValidationError as e:
            print(f"Validation error: {e}")
            return "Validation error"

        db = SessionLocal()
        db_info = CustomerInfoModel(
            thread_id=validated_info.thread_id,
            sender=validated_info.sender,
            content=validated_info.content,
            customer_name=validated_info.customer_name,
            contact_info=validated_info.contact_info,
            inquiry=validated_info.inquiry
        )
        db.add(db_info)
        db.commit()
        db.close()
        return "Customer info saved successfully"
    

    def analyze_sales_needs_task(self):
        return Task(
            description=dedent(f"""\
                Analyze sales-related emails to identify and understand customer needs and requirements.

                Use your expertise to determine the specific needs and potential opportunities presented in the emails.

                EMAILS
                -------
                {self.emails}
                Your final answer MUST be the analyzed sales needs and identified opportunities in the following format:
                - Need: {{need}}, Opportunity: {{opportunity}}
            """),
            agent=self.sales_agent,
            expected_output="Analyzed sales needs and identified opportunities in the specified format."
        )
    
    def save_sales_opportunity(self, sales_opportunity:dict):
        try:
            validated_opportunity = SalesOpportunity(**sales_opportunity)
        except ValidationError as e:
            print(f"Validation error: {e}")
            return "Validation error"

        db = SessionLocal()
        db_opportunity = SalesOpportunityModel(
            opportunity_id=validated_opportunity.opportunity_id,
            need=validated_opportunity.need,
            opportunity=validated_opportunity.opportunity
        )
        db.add(db_opportunity)
        db.commit()
        db.close()
        return "Sales opportunity saved successfully"
    
    def check_email_relevance_task(self):
        return Task(
            description=dedent(f"""\
                Determine if the email content is directly related to the user and requires an immediate response.
                Use your expertise to assess the urgency and relevance of the email content.
                EMAILS
                -------
                {self.emails}
                Your final answer MUST be a list of relevant thread IDs and the sender, use bullet points.
                - Thread ID: {{thread_id}}, Sender: {{sender}}, Requires Immediate Response: {{true/false}}
            """),
            agent=self.sales_agent,
            expected_output="List of relevant thread IDs and senders, indicating whether an immediate response is required."
        )

    def check_information_completeness_task(self):
        return Task(
            description=dedent(f"""\
                Check the completeness of the information provided in the sales-related emails.

                Use your expertise to determine if the information is sufficient to proceed or if additional details are needed.

                EMAILS
                -------
                {self.emails}

                Your final answer MUST be the completeness status of each email in the following format:
                - Thread ID: {{thread_id}}, Sender: {{sender}}, Information Complete: {{true/false}}
            """),
            agent=self.sales_agent,
            expected_output="Completeness status of each email in the specified format."
        )

    def handle_incomplete_information_task(self):
        return Task(
            description=dedent(f"""\
                Handle emails with incomplete information by defining the missing information and providing alternative suggestions.

                Use your expertise to suggest additional information or options that can help complete the request.

                EMAILS
                -------
                {self.emails}

                Your final answer MUST be the actions taken for each incomplete email in the following format:
                - Thread ID: {{thread_id}}, Sender: {{sender}}, Missing Information: {{missing_info}}, Suggested Options: {{options}}
            """),
            agent=self.sales_agent,
            expected_output="Actions taken for each incomplete email in the specified format."
        )


class InquiryTasks:
    def __init__(self, inquiry_agent, categorized_emails):
        self.inquiry_agent = inquiry_agent
        self.categorized_emails = categorized_emails

    def handle_inquiry_task(self):
        return Task(
            description=dedent(f"""\
                Analyze inquiry-related emails to identify and understand supplier inquiries and procurement needs.
                Use your expertise to determine the specific needs and potential suppliers.
                Categorized Emails
                -------
                {self.categorized_emails}
                Your final answer MUST be the analyzed inquiry details in the following format:
                - Inquiry: {{inquiry}}, Supplier: {{supplier}}, Product: {{product}}
            """),
            agent=self.inquiry_agent,
            expected_output="Analyzed inquiry details in the specified format."
        )

    def update_state_with_inquiry_info(self, result, state):
        state['inquiry_info'].extend(result['analyzed_inquiry_details'])

class ProductTasks:
    def __init__(self, product_agent, sales_info, inquiry_info):
        self.product_agent = product_agent
        self.sales_info = sales_info
        self.inquiry_info = inquiry_info

    def generate_strategy_task(self):
        return Task(
            description=dedent(f"""\
                Generate a product strategy based on sales information and inquiry details.
                Use your expertise to analyze the provided information and determine the best strategy for customer engagement or supplier negotiation.
                Sales Information
                -------
                {self.sales_info}
                Inquiry Information
                -------
                {self.inquiry_info}
                Your final answer MUST be the generated strategy in the following format:
                - Strategy: {{strategy}}
            """),
            agent=self.product_agent,
            expected_output="Generated strategy in the specified format."
        )

    def update_state_with_strategy(self, result, state):
        state['product_strategy'] = result['generated_strategy']


class DraftTasks:
    def __init__(self, draft_agent, product_strategy):
        self.draft_agent = draft_agent
        self.product_strategy = product_strategy

    def generate_email_task(self):
        return Task(
            description=dedent(f"""\
                Generate a professional email based on the provided product strategy.
                Use your expertise in email drafting to create a comprehensive and persuasive email.
                Product Strategy
                -------
                {self.product_strategy}
                Your final answer MUST be the generated email in the following format:
                - Email: {{email}}
            """),
            agent=self.draft_agent,
            expected_output="Generated email in the specified format."
        )

    def update_state_with_draft_email(self, result, state):
        state['draft_email'] = result['generated_email']

