import json
SP='nocoly/data'
D=json.load(open(SP+'/manifests.json'))
def closure(m,seen=None):
    if seen is None: seen=set()
    for d in D.get(m,{}).get('depends',[]):
        if d not in seen: seen.add(d); closure(d,seen)
    return seen
# platform-native in HAP — never become worksheets
NATIVE={'base','web','base_setup','bus','web_tour','html_editor','html_builder','http_routing',
 'auth_signup','portal','digest','onboarding','iap','mail_bot','google_recaptcha','social_media',
 'attachment_indexation','barcodes','barcodes_gs1_nomenclature','spreadsheet','gamification',
 'link_tracker','partner_autocomplete','google_address_autocomplete','iot_base','web_editor',
 'phone_validation','rating','portal_rating','website_mail','website_partner','website_profile',
 'mail','calendar','sms','resource_mail','onboarding','decimal_precision','product_images'}
ORDER=[('CRM','crm'),('Invoicing','account'),('Sales','sale'),('Purchase','purchase'),
       ('Inventory','stock'),('Manufacturing','mrp'),('Project','project')]
built=set()
print(f"{'Phase':<16}{'new modules introduced (worksheet-bearing)'}")
print("="*84)
for label,m in ORDER:
    cl=closure(m)|{m}
    new=sorted(x for x in cl-built if x not in NATIVE)
    built |= cl
    print(f"{label:<16}{', '.join(new) if new else '— nothing new —'}")
