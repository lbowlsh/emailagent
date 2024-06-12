
from crewai import Crew, Process
# from langchain_openai import ChatOpenAI
from agents import EmailAgents
# from email_filter.filteremailtasks import EmailFilterTasks
# from sales.salestask import SalesTasks,CustomerInfo,SalesOpportunity
from tasks import EmailFilterTasks,SalesTasks,InquiryTasks,ProductTasks,DraftTasks



class EmailProcessingCrew():
    def __init__(self):
        agents = EmailAgents()
        # self.filter_agent = agents.filter_agent
        self.category_agent = agents.category_agent    
        self.sales_agent= agents.sales_agent
        self.product_agent = agents.product_agent
        self.inquiry_agent = agents.inquiry_agent
        self.implementation_agent = agents.implementation_agent
        self.service_agent = agents.service_agent
        self.others_agent = agents.others_agent
        self.draft_agent = agents.draft_agent
        self.center_manager = agents.category_agent




    def kickoff(self, state):
        print("### Starting email processing workflow")

        emails = state['emails']  # Use emails from the state
        # category_tasks = filter_tasks(self.email_category, emails)
        category_tasks = EmailFilterTasks(self.category_agent, emails)
        categorized_emails_result = category_tasks.categorize_emails_task().execute(context=emails)

         # 打印返回值以进行调试
        print("categorized_emails_result:", categorized_emails_result)
        print("Type of categorized_emails_result:", type(categorized_emails_result))
        
        # Check if categorized_emails_result is a list
        if not isinstance(categorized_emails_result, list):
            raise TypeError("categorized_emails_result 应该是一个包含字典的列表")
    
    # Check if each item in the list is a dictionary
        for email in categorized_emails_result:
            if not isinstance(email, dict):
                raise TypeError("categorized_emails_result 中的每个元素应该是一个字典")

        sales_emails = [email for email in categorized_emails_result if email['category'] == 'Sales']
        state['categorized_emails']= categorized_emails_result

        inquiry_emails = [email for email in categorized_emails_result if email['category'] == 'Inquiry']

        sales_tasks = SalesTasks(self.sales_agent,emails)
        inquiry_tasks = InquiryTasks(self.inquiry_agent, inquiry_emails)
        product_tasks = ProductTasks(self.product_agent,state['sales_info'], state['inquiry_info'])
        darft_tasks = DraftTasks(self.draft_agent, state['product_strategy'])

        
        
        
        service_emails = [email for email in categorized_emails_result if email['category'] == 'Service']
        implementation_emails = [email for email in categorized_emails_result if email['category'] == 'Implementation']
        others_emails = [email for email in categorized_emails_result if email['category'] == 'Other']

        sales_tasks = SalesTasks(self.sales_agent, sales_emails)
        # inquiry_tasks = InquiryTasks(self.inquiry_agent, inquiry_emails)
        # service_tasks = ServiceTasks(self.service_agent, service_emails)
        # implementation_tasks = ImplementationTasks(self.implementation_agent, implementation_emails)
        # others_tasks = OthersTasks(self.others_agent, others_emails)


        crew = Crew(
            agents=[
                # self.filter_agent,
                self.category_agent,
                self.sales_agent,
                self.inquiry_agent,
                self.product_agent,
                self.draft_agent,
                self.implementation_agent,
                self.service_agent,
                self.others_agent
            ],
            tasks=[
                # filter_tasks.filter_emails_task(),
                category_tasks.categorize_emails_task(),
                sales_tasks.extract_customer_info_task(),
                sales_tasks.analyze_sales_needs_task(),
                sales_tasks.check_information_completeness_task(),
                sales_tasks.check_email_relevance_task(),
                sales_tasks.handle_incomplete_information_task(),
                inquiry_tasks.handle_inquiry_task(),
                product_tasks.generate_strategy_task(),
                darft_tasks.generate_email_task()
                
                


            ],
            process=Process.sequential,  # Ensure tasks are executed sequentially
            # verbose=True,
            # memory=True
        )
        result = crew.kickoff()
        sales_tasks.update_state_with_customer_info(result, state)
        inquiry_tasks.update_state_with_inquiry_info(result, state)
        product_tasks.update_state_with_strategy(result, state)
        darft_tasks.update_state_with_draft_email(result,state)

        # 打印结果以进行调试
        print("Result from Crew kickoff:", result)

        # return {**state, "action_required_emails": result}
    
        # 提取并保存客户信息
        extracted_info = result.get('extracted_customer_info',[])
        for info in extracted_info:
            customer_info = {
                "thread_id": info.get('thread_id'),
                "sender": info.get('sender'),
                "content": info.get('content'),
                "customer_name": info.get('customer_name'),
                "contact_info": info.get('contact_info'),
                "inquiry": info.get('inquiry')
            }
            save_result = sales_tasks.save_customer_info(customer_info)
            print("Save Customer Info Result:", save_result)  # 调试打印
            # sales_tasks.save_customer_info(customer_info)

        # 分析并保存商机
        analyzed_needs = result.get('analyzed_sales_needs',[])
        for opportunity in analyzed_needs:
            sales_opportunity = {
                "opportunity_id": opportunity.get('opportunity_id'),
                "need": opportunity.get('need'),
                "opportunity": opportunity.get('opportunity')
            }
            save_opportunity_result = sales_tasks.save_opportunity(sales_opportunity)
            print("Save Sales Opportunity Result:", save_opportunity_result)  # 调试打印

            #sales_tasks.save_sales_opportunity(sales_opportunity)
        
            # return {**state, "action_required_emails": result}




    def _format_emails(self, emails):
        emails_string = []
        for email in emails:
            print(email)
            arr = [
                f"ID: {email['id']}",
                f"- Thread ID: {email['threadId']}",
                f"- Snippet: {email['snippet']}",
                f"- From: {email['sender']}",
                f"--------"
            ]
            emails_string.append("\n".join(arr))
        return "\n".join(emails_string)

state = {
    'emails': [
        {'id': '1', 'threadId': '12345', 'snippet': 'Meeting at 3 PM', 'sender': 'sales@example.com'},
        {'id': '2', 'threadId': '67890', 'snippet': '50% off on your next purchase', 'sender': 'promo@example.com'},
        {'id': '3', 'threadId': '13579', 'snippet': 'Interview Schedule', 'sender': 'hr@example.com'}
    ]
}

# 初始化并启动工作流
email_processing_crew = EmailProcessingCrew()
result = email_processing_crew.kickoff(state)

# 打印结果
print("Final Result:", result)