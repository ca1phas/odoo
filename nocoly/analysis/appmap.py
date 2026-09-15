import json
SP='nocoly/data'
D=json.load(open(SP+'/manifests.json'))
CAT={
 "Website":[("Website","website"),("eCommerce","website_sale"),("Blog","website_blog"),
            ("Forum","website_forum"),("eLearning","website_slides"),("Live Chat","im_livechat")],
 "Sales":[("CRM","crm"),("Sales","sale_management"),("Point of Sale","point_of_sale"),
          ("Subscriptions","sale_subscription"),("Rental","sale_renting")],
 "Finance":[("Accounting","account_accountant"),("Invoicing","account"),("Expenses","hr_expense"),
            ("Documents","documents"),("Spreadsheets","spreadsheet"),("Sign","sign"),("ESG","esg")],
 "Inventory & Manufacturing":[("Inventory","stock"),("Manufacturing","mrp"),("PLM","mrp_plm"),
            ("Purchase","purchase"),("Maintenance","maintenance"),("Quality","quality_control")],
 "Human Resources":[("Employees","hr"),("Recruitment","hr_recruitment"),("Time Off","hr_holidays"),
            ("Appraisals","hr_appraisal"),("Referral","hr_referral"),("Fleet","fleet")],
 "Marketing":[("Marketing Automation","marketing_automation"),("Email Marketing","mass_mailing"),
            ("SMS Marketing","mass_mailing_sms"),("Social Marketing","social"),
            ("Events","event"),("Survey","survey")],
 "Services":[("Project","project"),("Timesheet","hr_timesheet"),("Field Service","industry_fsm"),
            ("Helpdesk","helpdesk"),("Planning","planning"),("Appointments","appointment")],
 "Productivity":[("Discuss","mail"),("Approvals","approvals"),("Internet of Things","iot"),
            ("VOIP","voip"),("Knowledge","knowledge"),("AI","ai")],
 "Customization":[("Studio","web_studio")],
}
present=missing=0
for cat,apps in CAT.items():
    print(f"\n## {cat}")
    for label,mod in apps:
        if mod in D:
            present+=1
            print(f"  [OK]      {label:<22} -> {mod:<22} depends={D[mod]['depends']}")
        else:
            missing+=1
            print(f"  [ABSENT]  {label:<22} -> {mod}")
print(f"\nin repo: {present}   not in repo (Enterprise): {missing}")
