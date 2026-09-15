const HOURS={"core":47.9,"bundles":{"btax":3.0,"bcoa":4.2,"bcat":1.1,"bterm":4.9,"bpay":15.4,"bvar":12.0,"bpl":9.8,"butm":3.4,"bteam":3.0,"bana":6.0,"bplan":3.4,"bgeo":3.5,"bfp":6.8,"binc":1.1,"bcur":1.1,"bcombo":4.1,"btag":1.1},"bundleApp":16.2,"phases":{"2":35.8,"3":73.1,"4":76.6,"5":287.5,"6":96.6,"7":184.4,"8":48.9,"9":164.6,"10":367.0,"11":19.6},"week":40.0};
/* [id, name, sublabel, deps, count] */
const CORE=[
 ['contacts','Contacts','res.partner',[]],
 ['units','Units & Packagings','uom.uom',[]],
 ['products','Products','product.template',['categories','units']],
 ['variants','Product Variants','product.product',['products']],
 ['journals','Journals','account.journal',['accounts']],
 ['invoices','Invoices','account.move',['contacts','journals','terms']],
 ['invlines','Invoice Lines','account.move.line',['invoices','variants','units','taxes','accounts']],
];
const BUNDLES=[
 ['btax','Taxes','—','the first invoice that carries tax — in practice, day one',[
   ['taxes','Taxes','account.tax',['!countries','accounts']]]],
 ['bcoa','Chart of Accounts','—','real double-entry — Phase 8 Finance',[
   ['accounts','Chart of Accounts','account.account',[]]]],
 ['bcat','Product Categories','—','product reporting and stock valuation',[
   ['categories','Product Categories','product.category',[]]]],
 ['bterm','Payment Terms','—','any due date beyond immediate payment',[
   ['terms','Payment Terms','account.payment.term',[]]]],
 ['bpay','Payments','—','receipts as records rather than a paid-amount field',[
   ['paymeth','Payment Methods','account.payment.method',[]],
   ['payments','Payments','account.payment',['invoices','contacts','journals','paymeth']]]],
 ['bvar','Product Variants','product.group_product_variant','first product with options',[
   ['attrs','Attributes','product.attribute',[]],
   ['attrvals','Attribute Values','product.attribute.value',['attrs']],
   ['attrlines','Product Attribute Lines','product.template.attribute.line',['products','attrs','attrvals']],
   ['tav','Template Attribute Values','product.template.attribute.value',['attrlines','attrvals','variants']]]],
 ['bpl','Pricelists','product.group_product_pricelist','Phase 3 · Sales',[
   ['pricelists','Pricelists','product.pricelist',[]],
   ['pricerules','Price Rules','product.pricelist.item',['pricelists','products','variants','categories']]]],
 ['butm','Marketing attribution','—','Phase 2 · CRM',[
   ['campaigns','Campaigns','utm.campaign',[]],
   ['sources','Sources','utm.source',[]],
   ['mediums','Mediums','utm.medium',[]]]],
 ['bteam','Sales Teams','—','Phase 2 · CRM',[
   ['teams','Sales Teams','crm.team',[]]]],
 ['bana','Analytic Accounting','analytic.group_analytic_accounting','Phase 6 · Services',[
   ['anaacc','Analytic Accounts','account.analytic.account',['contacts']],
   ['analine','Analytic Lines','account.analytic.line',['anaacc','variants','units']]]],
 ['bgeo','Geography','—','before Fiscal Positions',[
   ['countries','Countries','res.country',[]],
   ['states','States','res.country.state',['countries']]]],
 ['bfp','Fiscal Positions','—','first exempt customer',[
   ['fiscal','Fiscal Positions','account.fiscal.position',['!countries','!taxes','accounts']]]],
 ['binc','Incoterms','—','first international shipment',[
   ['incoterms','Incoterms','account.incoterms',[]]]],
 ['bcur','Multi-currency','base.group_multi_currency','second currency',[
   ['currencies','Currencies','res.currency',[]]]],
 ['bcombo','Product Combos','—','Phase 4 · Point of Sale',[
   ['combos','Combo Choices','product.combo',[]],
   ['comboitems','Combo Items','product.combo.item',['combos','variants']]]],
 ['bplan','Activities','—','first scheduled follow-up',[
   ['acttypes','Activity Types','mail.activity.type',[]],
   ['actplans','Activity Plans','mail.activity.plan',[]],
   ['actsteps','Plan Steps','mail.activity.plan.template',['actplans','acttypes']]]],
 ['btag','Contact Tags','—','first segmented mailing',[
   ['tags','Contact Tags','res.partner.category',[]]]],
];
const PHASES=[
 [2,'CRM',[
   ['stages','Stages','crm.stage',['teams']],
   ['lost','Lost Reasons','crm.lost.reason',[]],
   ['recur','Recurring Plans','crm.recurring.plan',[]],
   ['leads','Leads','crm.lead',['contacts','stages','teams','lost','recur','campaigns','sources','mediums','tags']]]],
 [3,'Sales',[
   ['qtpl','Quotation Templates','sale.order.template',[]],
   ['qtpll','Template Lines','sale.order.template.line',['qtpl','variants','units']],
   ['orders','Orders','sale.order',['contacts','pricelists','terms','fiscal','incoterms','teams','campaigns','qtpl','anaacc','leads','invoices']],
   ['ordl','Order Lines','sale.order.line',['orders','variants','units','taxes']],
   ['hdr','Headers / Footers','sale.pdf.form.field',[]]]],
 [4,'Point of Sale',[
   ['pospm','POS Payment Methods','pos.payment.method',['journals']],
   ['poscfg','POS Configs','pos.config',['journals','pospm','stock']],
   ['possess','Sessions','pos.session',['poscfg']],
   ['posord','POS Orders','pos.order',['possess','contacts','stock']],
   ['posline','POS Order Lines','pos.order.line',['posord','variants','taxes']],
   ['pospay','POS Payments','pos.payment',['posord','pospm']],
   ['poscat','POS Categories','pos.category',[]],
   ['posbill','Bills','pos.bill',[]],
   ['posnote','Notes','pos.note',[]],
   ['pospre','Presets','pos.preset',[]],
   ['posprn','Printers','pos.printer',[]],
   ['poslot','Pack Operation Lots','pos.pack.operation.lot',['posline','stock']]]],
 [5,'Inventory & Manufacturing',[
   ['purchase','Purchase','3 worksheets',['contacts','variants','units','taxes','terms','invoices'],3],
   ['stock','Inventory','21 worksheets',['variants','units','contacts'],21],
   ['mrp','Manufacturing','14 worksheets',['variants','units','stock'],14],
   ['maint','Maintenance','5 worksheets',['contacts'],5],
   ['repair','Repair','2 worksheets',['variants','contacts','stock'],2]]],
 [6,'Services',[
   ['project','Project','11 worksheets',['contacts','anaacc'],11],
   ['timesheet','Timesheet','1 worksheet',['anaacc','project'],1]]],
 [7,'Human Resources',[
   ['hr','Employees','10 worksheets',['contacts'],10],
   ['recruit','Recruitment','8 worksheets',['contacts','hr'],8],
   ['timeoff','Time Off','6 worksheets',['hr'],6],
   ['fleet','Fleet','11 worksheets',['contacts','hr'],11]]],
 [8,'Finance',[
   ['expense','Expenses','2 worksheets',['hr','variants','taxes','invoices','anaacc'],2],
   ['bankst','Bank Statements','1 worksheet',['journals'],1],
   ['recon','Reconciliation','1 worksheet',['invoices','journals'],1]]],
 [9,'Marketing',[
   ['mailing','Email Marketing','7 worksheets',['contacts','campaigns','sources','mediums'],7],
   ['events','Events','16 worksheets',['contacts','variants','invoices'],16],
   ['survey','Survey','5 worksheets',['contacts'],5]]],
 [10,'Website',[
   ['website','Website','12 worksheets',[],12],
   ['ecom','eCommerce','8 worksheets',['orders','variants','pricelists','stock'],8],
   ['slides','eLearning','11 worksheets',['contacts','website'],11],
   ['livechat','Live Chat','9 worksheets',['contacts','website'],9],
   ['forum','Forum','5 worksheets',['contacts','website'],5],
   ['blog','Blog','4 worksheets',['website'],4]]],
 [11,'Productivity',[
   ['discuss','Discuss','3 worksheets',[],3]]],
];
